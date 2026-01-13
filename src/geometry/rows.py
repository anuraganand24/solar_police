# src/geometry/rows.py

import cv2
import numpy as np

def detect_row_mask(rgb_tile):
    """
    Detects panel row regions using edge density.
    This avoids ground / gravel false positives.
    """

    # 1. Convert to grayscale
    gray = cv2.cvtColor(rgb_tile, cv2.COLOR_BGR2GRAY)

    # 2. Light blur to suppress noise
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Edge detection (panels have strong grid edges)
    edges = cv2.Canny(gray, 50, 150)

    # 4. Dilate edges horizontally (rows are long)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 3))
    edge_band = cv2.dilate(edges, kernel, iterations=1)

    # 5. Remove tiny noise
    edge_band = cv2.morphologyEx(
        edge_band,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    )

    return edge_band

# src/geometry/rows.py


def fill_panel_mask(row_mask):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 7))

    # Strong horizontal closing
    closed = cv2.morphologyEx(
        row_mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=3
    )

    # Remove thin junk
    closed = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    )

    contours, _ = cv2.findContours(
        closed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    mask = np.zeros_like(closed, dtype=np.uint8)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        # 👇 panel rows are long & thin
        if w < 200 or h < 20:
            continue

        cv2.rectangle(mask, (x, y), (x + w, y + h), 1, -1)

    return mask.astype(bool)
