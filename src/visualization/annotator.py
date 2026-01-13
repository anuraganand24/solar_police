# src/visualization/annotator.py

import cv2

SEVERITY_COLORS = {
    "CRITICAL": (0, 0, 255),     # Red
    "HIGH":     (0, 165, 255),   # Orange
    "MEDIUM":   (0, 255, 255),   # Yellow
    "LOW":      (0, 255, 0),     # Green
}


def annotate_tile(
    image,
    faults,
    tile_id,
    output_path
):
    """
    Bounding-box accurate overlays for ONE tile.
    """

    vis = image.copy()

    # Normalize for viewing if needed
    if vis.dtype != "uint8":
        vis = cv2.normalize(vis, None, 0, 255, cv2.NORM_MINMAX)
        vis = vis.astype("uint8")

    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

    for f in faults:
        if f.get("tile_id") != tile_id:
            continue

        if "bbox" not in f:
            continue

        b = f["bbox"]
        color = SEVERITY_COLORS.get(f["severity"], (255, 255, 255))

        x1, y1 = b["x_min"], b["y_min"]
        x2, y2 = b["x_max"], b["y_max"]

        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)

        label = f"{f['severity']} | ΔT={f['delta_t_max']:.1f}"

        cv2.putText(
            vis,
            label,
            (x1, max(y1 - 5, 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
            cv2.LINE_AA
        )

    cv2.imwrite(output_path, vis)
