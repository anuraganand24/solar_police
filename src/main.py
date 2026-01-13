# src/main.py

from tqdm import tqdm
import numpy as np
import sys
import os

from src.io.tiff_reader import open_tiff
from src.io.tile_generator import generate_tiles

from src.thermal.normalization import normalize_ir_tile
from src.geometry.orientation import estimate_row_orientation
from src.geometry.rows import detect_row_mask, fill_panel_mask
from src.geometry.panels import extract_panel_rois

from src.faults.detector import detect_faults
from src.faults.merger import merge_faults_spatially
from src.faults.exporter import export_csv, export_geojson
from src.faults.classifier import classify_fault

from src.visualization.annotator import annotate_tile
from src.geometry.mask_utils import resize_mask_to_ir
from src.faults.priority import compute_priority

from src.config import (
    IR_PATH,
    IR_BAND_INDEX,
    RGB_PATH,
    FAULTS_CSV,
    FAULTS_GEOJSON,
)

from src.utils.logger import get_logger

logger = get_logger()

# =========================
# Global controls
# =========================
LOG_EVERY_N = 200
MAX_DEBUG_TILES = 200
MAX_ANNOTATED_TILES = 200   # avoid thousands of PNGs


# ============================================================
# STEP 2 — IR radiometric normalization (LOCKED)
# ============================================================
def run_step2():
    logger.info("STEP-2 STARTED: IR radiometric normalization")

    ds = open_tiff(IR_PATH)
    total_tiles, non_zero_tiles = 0, 0

    for idx, item in enumerate(
        tqdm(generate_tiles(ds, band_index=IR_BAND_INDEX))
    ):
        ir_tile = item["tile"]
        if ir_tile is None or ir_tile.size == 0:
            continue

        ir_tile = ir_tile.astype("float32")
        total_tiles += 1

        if ir_tile.max() > 0:
            non_zero_tiles += 1
            _, stats = normalize_ir_tile(ir_tile)

            if idx < MAX_DEBUG_TILES and stats:
                logger.info(
                    f"[STEP-2] Tile {idx} | "
                    f"median={stats['bg_median']:.2f}, "
                    f"std={stats['bg_std']:.2f}"
                )

    ds.close()

    logger.info(
        f"[STEP-2] Completed | Tiles={total_tiles}, Valid={non_zero_tiles}"
    )


# ============================================================
# STEP 3 — Panel geometry detection (RGB)
# ============================================================
def run_step3():
    logger.info("STEP-3 STARTED: Panel geometry detection")

    ds = open_tiff(RGB_PATH)

    for idx, item in enumerate(
        tqdm(generate_tiles(ds, band_indices=[1, 2, 3]))
    ):
        rgb_tile = item["tile"]
        if rgb_tile is None or rgb_tile.shape[-1] != 3:
            continue

        angle = estimate_row_orientation(rgb_tile)
        row_mask = detect_row_mask(rgb_tile)
        extract_panel_rois(row_mask)

        if idx < MAX_DEBUG_TILES:
            logger.info(f"[STEP-3] Tile {idx} | angle={angle}")

    ds.close()
    logger.info("[STEP-3] COMPLETED")


# ============================================================
# STEP 4 + 5.5 + 6 — Detect → Merge → Classify → Annotate
# ============================================================
def run_step4():
    logger.info("STEP-4 STARTED: Thermal fault detection")

    os.makedirs("outputs/annotated/ir", exist_ok=True)

    ir_ds = open_tiff(IR_PATH)
    rgb_ds = open_tiff(RGB_PATH)

    all_faults = []
    tile_id = 0

    ir_tiles = generate_tiles(ir_ds, band_index=IR_BAND_INDEX)
    rgb_tiles = generate_tiles(rgb_ds, band_indices=[1, 2, 3])

    for ir_item, rgb_item in tqdm(
        zip(ir_tiles, rgb_tiles),
        desc="STEP-4 | IR + RGB tiles"
    ):
        ir_tile = ir_item["tile"]
        transform = ir_item["transform"]
        rgb_tile = rgb_item["tile"]

        if (
            ir_tile is None or ir_tile.size == 0 or
            rgb_tile is None or rgb_tile.ndim != 3
        ):
            tile_id += 1
            continue

        # --------------------------------------------------
        # STEP 2 — Normalize IR → ΔT
        # --------------------------------------------------
        delta_t, stats = normalize_ir_tile(ir_tile)

        if (
            delta_t is None
            or stats is None
            or not np.isfinite(delta_t).any()
        ):
            tile_id += 1
            continue

        # --------------------------------------------------
        # STEP 3 → 4 BRIDGE: PANEL MASK (CRITICAL)
        # --------------------------------------------------
        row_mask = detect_row_mask(rgb_tile)
        panel_mask_rgb = fill_panel_mask(row_mask)

        panel_mask_ir = resize_mask_to_ir(
            panel_mask_rgb,
            delta_t.shape
        )

        # 🔍 DEBUG (first few tiles only)
        if tile_id < 5:
            logger.info(
                f"[DEBUG] Tile {tile_id} | "
                f"panel_pixels={panel_mask_ir.sum()} | "
                f"coverage={panel_mask_ir.mean():.3f}"
            )

        if panel_mask_ir.sum() < 100:
            # fallback: do not mask this tile
            panel_mask_ir = None


        # --------------------------------------------------
        # STEP 4 — Fault detection (panel constrained)
        # --------------------------------------------------
        faults = detect_faults(
            delta_t=delta_t,
            transform=transform,
            tile_id=tile_id,
            panel_mask=panel_mask_ir
        )

        all_faults.extend(faults)

        # --------------------------------------------------
        # STEP 6.2 — Annotated overlays (tile-level)
        # --------------------------------------------------
        if tile_id < MAX_ANNOTATED_TILES:
            annotate_tile(
                image=ir_tile,
                faults=faults,
                tile_id=tile_id,
                output_path=f"outputs/annotated/ir/tile_{tile_id:04d}.png"
            )

        tile_id += 1

    ir_ds.close()
    rgb_ds.close()

    logger.info(
        f"[STEP-4] Tile-level detections: {len(all_faults)}"
    )

    # --------------------------------------------------
    # STEP 5.5 — Spatial merging
    # --------------------------------------------------
    merged_faults = merge_faults_spatially(all_faults)


    # --------------------------------------------------
    # STEP 6.0 — Priority scoring (NEW)
    # --------------------------------------------------
    for f in merged_faults:
        f["priority"] = compute_priority(f)


    # --------------------------------------------------
    # STEP 6.0 — Severity-based reporting filter
    # --------------------------------------------------
    REPORTED_SEVERITIES = {"MEDIUM", "HIGH", "CRITICAL"}

    filtered_faults = [
        f for f in merged_faults
        if f["severity"] in REPORTED_SEVERITIES
    ]

    logger.info(
        f"[REPORT FILTER] "
        f"Before={len(merged_faults)} | "
        f"Reported={len(filtered_faults)}"
    )


    # --------------------------------------------------
    # STEP 6.1 — Final classification
    # --------------------------------------------------
    for f in merged_faults:
        f["fault_type"] = classify_fault(f)

    from collections import Counter
    logger.info(
        f"[FINAL SEVERITY] {Counter(f['severity'] for f in merged_faults)}"
    )

    merged_faults.sort(
    key=lambda x: x["priority"],
    reverse=True
        )

    # --------------------------------------------------
    # STEP 6 — Export
    # --------------------------------------------------
    export_csv(merged_faults, FAULTS_CSV)
    export_geojson(merged_faults, FAULTS_GEOJSON)

    logger.info(
        f"PIPELINE COMPLETED | "
        f"Tiles={tile_id} | Physical faults={len(merged_faults)}"
    )
# ============================================================
# Entry point
# ============================================================
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "\nUsage:\n"
            "  python -m src.main step2\n"
            "  python -m src.main step3\n"
            "  python -m src.main step4\n"
        )
        sys.exit(1)

    step = sys.argv[1].lower()

    if step == "step2":
        run_step2()
    elif step == "step3":
        run_step3()
    elif step == "step4":
        run_step4()
    else:
        print(f"Unknown step: {step}")
        sys.exit(1)
