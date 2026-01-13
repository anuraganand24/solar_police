# src/faults/confidence.py

def compute_confidence(delta_t_max, pixel_area, zscore_max):
    severity_score = max(0.0, min(1.0, (delta_t_max - 5.0) / 35.0))
    spatial_score = max(0.0, min(1.0, pixel_area / 500.0))

    # 🔒 HARD CAP when no statistical support
    if zscore_max is None or zscore_max == 0.0:
        stat_score = 0.25   # ← critical fix
    else:
        stat_score = min(1.0, zscore_max / 5.0)

    confidence = (
        0.45 * severity_score +
        0.30 * spatial_score +
        0.25 * stat_score
    ) * 100.0

    return round(min(confidence, 85.0), 1)  # ← cap
