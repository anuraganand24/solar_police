# src/faults/detector.py

import numpy as np
import cv2
from src.faults.confidence import compute_confidence

# --------------------------------------------------
# Detection thresholds (LOCAL ΔT based)
# --------------------------------------------------
LOCAL_DT_THRESHOLD = 7.5
MIN_CLUSTER_AREA = 120
MAX_CLUSTER_AREA = 2000
BORDER_PAD = 8


def detect_faults(delta_t, transform, tile_id, panel_mask=None):
    """
    Detect thermal faults in ONE IR tile.
    """

    faults = []

    if delta_t is None:
        return faults

    if delta_t.ndim == 3:
        delta_t = delta_t[:, :, 0]

    h, w = delta_t.shape

    # --------------------------------------------------
    # Panel mask fail-safe
    # --------------------------------------------------
    if panel_mask is not None:
        if panel_mask.shape != delta_t.shape or panel_mask.sum() < 50:
            panel_mask = None

    # --------------------------------------------------
    # LOCAL BASELINE REMOVAL
    # --------------------------------------------------
    baseline = cv2.GaussianBlur(delta_t, (51, 51), 0)
    delta_local = delta_t - baseline

    # --------------------------------------------------
    # Hotspot mask
    # --------------------------------------------------
    hotspot_mask = (
        (delta_local > LOCAL_DT_THRESHOLD) &
        (panel_mask if panel_mask is not None else True)
    ).astype(np.uint8)

    # --------------------------------------------------
    # TILE BORDER SUPPRESSION
    # --------------------------------------------------
    hotspot_mask[:BORDER_PAD, :] = 0
    hotspot_mask[-BORDER_PAD:, :] = 0
    hotspot_mask[:, :BORDER_PAD] = 0
    hotspot_mask[:, -BORDER_PAD:] = 0

    if hotspot_mask.sum() == 0:
        return faults

    # --------------------------------------------------
    # Connected components
    # --------------------------------------------------
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        hotspot_mask, connectivity=8
    )

    for label in range(1, num_labels):

        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < MIN_CLUSTER_AREA or area > MAX_CLUSTER_AREA:
            continue

        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w_box = int(stats[label, cv2.CC_STAT_WIDTH])
        h_box = int(stats[label, cv2.CC_STAT_HEIGHT])

        # --------------------------------------------------
        # EDGE-CLUSTER REJECTION
        # --------------------------------------------------
        if (
            x <= BORDER_PAD or
            y <= BORDER_PAD or
            x + w_box >= w - BORDER_PAD or
            y + h_box >= h - BORDER_PAD
        ):
            continue

        # --------------------------------------------------
        # TILE-SPANNING REJECTION (CRITICAL FIX)
        # --------------------------------------------------
        if w_box > 0.85 * w or h_box > 0.85 * h:
            continue

        bbox = {
            "x_min": x,
            "y_min": y,
            "x_max": x + w_box,
            "y_max": y + h_box,
        }

        # --------------------------------------------------
        # GEOMETRIC FILTER
        # --------------------------------------------------
        aspect_ratio = w_box / max(h_box, 1)
        if aspect_ratio > 6.0 or aspect_ratio < 0.15:
            continue

        cluster_mask = labels == label

        # --------------------------------------------------
        # PHYSICS
        # --------------------------------------------------
        peak_local_dt = float(delta_local[cluster_mask].max())
        mean_local = float(delta_local[cluster_mask].mean())
        peak_raw_dt = float(delta_t[cluster_mask].max())

        # Reject diffuse heating
        if mean_local <= 0.6 * peak_local_dt:
            continue

        # --------------------------------------------------
        # GEO
        # --------------------------------------------------
        cx, cy = centroids[label]
        lon, lat = transform * (int(cx), int(cy))

        # --------------------------------------------------
        # Tile-level severity
        # --------------------------------------------------
        severity = (
            "HIGH"   if peak_local_dt >= 12.0 else
            "MEDIUM" if peak_local_dt >= 8.0 else
            "LOW"
        )

        confidence = compute_confidence(
            delta_t_max=peak_local_dt,
            pixel_area=area,
            zscore_max=0.0,
        )

        faults.append({
            "tile_id": tile_id,
            "fault_type": "HOTSPOT",   # refined post-merge
            "severity": severity,
            "confidence": confidence,

            # Physics
            "delta_t_max": round(peak_raw_dt, 2),
            "zscore_max": 0.0,
            "pixel_area": area,

            # Geometry
            "lon": float(lon),
            "lat": float(lat),
            "bbox": bbox,
        })

    return faults
