# src/geometry/orientation.py

import cv2
import numpy as np

def estimate_row_orientation(rgb_tile):
    """
    Estimates dominant panel row angle in degrees.
    Returns angle in range [-90, 90].
    """

    gray = cv2.cvtColor(rgb_tile, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=150)

    if lines is None:
        return None

    angles = []

    for line in lines[:50]:  # limit for stability
        rho, theta = line[0]
        angle = (theta - np.pi / 2) * 180 / np.pi
        angles.append(angle)

    return float(np.median(angles))
