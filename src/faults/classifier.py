# src/faults/classifier.py

def classify_fault(fault):
    area = fault["pixel_area"]
    dt = fault["delta_t_max"]
    severity = fault["severity"]

    # ---------------------------------------
    # Cell hotspot
    # ---------------------------------------
    if area < 120 and dt >= 36:
        return "CELL_HOTSPOT"

    # ---------------------------------------
    # Junction box hotspot
    # ---------------------------------------
    if area >= 600 and dt >= 38:
        return "JUNCTION_BOX_HOTSPOT"

    # ---------------------------------------
    # 🔥 CRITICAL override (IMPORTANT)
    # ---------------------------------------
    if severity == "CRITICAL":
        return "JUNCTION_BOX_HOTSPOT"

    # ---------------------------------------
    # Default
    # ---------------------------------------
    return "PANEL_HOTSPOT"
