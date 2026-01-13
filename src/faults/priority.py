import math

def compute_priority(fault):
    severity_weight = {
        "CRITICAL": 2.0,
        "HIGH": 1.5,
        "MEDIUM": 1.0,
        "LOW": 0.6,
    }.get(fault["severity"], 1.0)

    return round(
        severity_weight
        * fault["confidence"]
        * math.log1p(fault["pixel_area"]),
        2
    )
