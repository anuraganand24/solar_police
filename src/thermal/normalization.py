# src/thermal/normalization.py

import numpy as np

def normalize_ir_tile(ir_tile, clip_sigma=3.0):
    """
    Converts raw IR tile to delta-T (ΔT) map using background reference.
    """

    if ir_tile.ndim == 3:
        ir_tile = ir_tile[:, :, 0]

    ir_tile = ir_tile.astype("float32")

    # Ignore invalid / masked pixels
    valid = ir_tile > 0
    if valid.sum() < 50:
        # fallback: treat entire tile as valid
        background = ir_tile
    else:
        background = ir_tile[valid]


    background = ir_tile[valid]

    bg_median = np.median(background)
    bg_std = np.std(background)

    if bg_std < 1e-6:
        bg_std = 1.0 

    # Clip extreme outliers
    lower = bg_median - clip_sigma * bg_std
    upper = bg_median + clip_sigma * bg_std
    ir_clipped = np.clip(ir_tile, lower, upper)

    # ΔT relative to background
    delta_t = ir_clipped - bg_median

    stats = {
        "bg_median": float(bg_median),
        "bg_std": float(bg_std),
        "dt_min": float(delta_t.min()),
        "dt_max": float(delta_t.max()),
    }

    return delta_t, stats
