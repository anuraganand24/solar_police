# src/faults/merger.py

import numpy as np
from src.faults.confidence import compute_confidence

MERGE_DISTANCE_METERS = 6.0

# ---------------------------------------------
# Energy loss model (safe, bounded, defensible)
# ---------------------------------------------
def estimate_energy_loss(delta_t, area, panel_kw=0.54, annual_yield=1650):
    """
    Estimate annual energy loss due to thermal fault.
    Returns (loss_pct, annual_kwh_loss)
    """

    # Fractional power loss (bounded)
    loss_fraction = 0.002 * delta_t * (area / 100.0) ** 0.5
    loss_fraction = min(max(loss_fraction, 0.0), 0.35)

    annual_kwh_loss = panel_kw * annual_yield * loss_fraction

    return round(loss_fraction * 100, 2), round(annual_kwh_loss, 1)


def _distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _classify_fault(delta_t_max, pixel_area, merge_count):
    if merge_count >= 2 and pixel_area >= 400 and delta_t_max >= 30:
        return "JUNCTION_BOX_HOTSPOT"
    elif pixel_area < 150 and delta_t_max >= 35:
        return "CELL_HOTSPOT"
    else:
        return "PANEL_HOTSPOT"


def _severity_from_physics(delta_t_max, pixel_area):
    if delta_t_max >= 40 and pixel_area >= 400:
        return "CRITICAL"
    elif delta_t_max >= 30:
        return "HIGH"
    elif delta_t_max >= 20:
        return "MEDIUM"
    else:
        return "LOW"


def _merge_bboxes(bboxes):
    return {
        "x_min": min(b["x_min"] for b in bboxes),
        "y_min": min(b["y_min"] for b in bboxes),
        "x_max": max(b["x_max"] for b in bboxes),
        "y_max": max(b["y_max"] for b in bboxes),
    }


def _aggregate_cluster(cluster, fault_id):
    areas = np.array([c["pixel_area"] for c in cluster], dtype=np.float32)
    total_area = float(areas.sum())

    if total_area <= 0:
        return None

    # Area-weighted centroid
    lon = float(sum(c["lon"] * a for c, a in zip(cluster, areas)) / total_area)
    lat = float(sum(c["lat"] * a for c, a in zip(cluster, areas)) / total_area)

    # Worst-case physics
    delta_t_max = float(max(c["delta_t_max"] for c in cluster))
    merge_count = len(cluster)

    zscores = [
        c.get("zscore_max", 0.0)
        for c in cluster
        if isinstance(c.get("zscore_max"), (int, float))
    ]
    zscore_max = float(max(zscores)) if zscores else 0.0

    # Classification
    fault_type = _classify_fault(delta_t_max, total_area, merge_count)
    severity = _severity_from_physics(delta_t_max, total_area)

    confidence = compute_confidence(
        delta_t_max=delta_t_max,
        pixel_area=int(total_area),
        zscore_max=zscore_max,
    )

    # 🔥 Energy loss estimation (NEW)
    loss_pct, annual_kwh_loss = estimate_energy_loss(
        delta_t=delta_t_max,
        area=total_area
    )

    return {
        "fault_id": f"F-{fault_id:04d}",
        "fault_type": fault_type,
        "severity": severity,
        "confidence": confidence,

        # Physics
        "delta_t_max": round(delta_t_max, 2),
        "zscore_max": zscore_max,
        "pixel_area": int(total_area),
        "merge_count": merge_count,

        # Energy impact (NEW)
        "loss_pct": loss_pct,
        "annual_kwh_loss": annual_kwh_loss,

        # Geometry
        "lon": lon,
        "lat": lat,
        "bbox": _merge_bboxes([c["bbox"] for c in cluster]),
        "tiles": sorted(
            {c["tile_id"] for c in cluster if "tile_id" in c}
        ),
    }


def merge_faults_spatially(faults):
    if not faults:
        return []

    remaining = list(faults)
    merged_any = True
    fault_id = 0

    while merged_any:
        merged_any = False
        clusters = []
        used = set()

        for i, f in enumerate(remaining):
            if i in used:
                continue

            cluster = [f]
            used.add(i)

            for j, g in enumerate(remaining):
                if j in used:
                    continue

                if _distance(
                    (f["lon"], f["lat"]),
                    (g["lon"], g["lat"])
                ) <= MERGE_DISTANCE_METERS:
                    cluster.append(g)
                    used.add(j)
                    merged_any = True

            clusters.append(cluster)

        remaining = []
        for c in clusters:
            agg = _aggregate_cluster(c, fault_id)
            if agg is not None:
                remaining.append(agg)
                fault_id += 1

    return remaining
