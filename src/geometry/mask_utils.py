# src/geometry/mask_utils.py

import cv2
import numpy as np


def resize_mask_to_ir(panel_mask_rgb, ir_shape):
    """
    Resizes RGB-derived panel mask to IR tile resolution.

    panel_mask_rgb : 2D uint8 or bool mask (RGB tile space)
    ir_shape       : (H, W) of IR tile

    Returns:
        panel_mask_ir : boolean mask aligned to IR tile
    """

    ir_h, ir_w = ir_shape

    resized = cv2.resize(
        panel_mask_rgb.astype("uint8"),
        (ir_w, ir_h),
        interpolation=cv2.INTER_NEAREST
    )

    return resized.astype(bool)
