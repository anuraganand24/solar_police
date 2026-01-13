# src/geometry/panels.py

import cv2

def extract_panel_rois(row_mask, min_area=5000):
    """
    Extracts rectangular ROIs from row mask.
    Returns list of bounding boxes.
    """

    contours, _ = cv2.findContours(
        row_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    rois = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        rois.append((x, y, w, h))

    return rois
