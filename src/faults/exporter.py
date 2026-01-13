# src/faults/exporter.py

import csv
import json


def export_csv(faults, path):
    if not faults:
        return

    keys = faults[0].keys()

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(faults)


def export_geojson(faults, path):
    features = []

    for f in faults:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [f["lon"], f["lat"]]
            },
            "properties": {
                "fault_id": f["fault_id"],
                "fault_type": f["fault_type"],
                "severity": f["severity"],
                "confidence": f["confidence"],
                "delta_t_max": f["delta_t_max"],
                "zscore_max": f.get("zscore_max"),  # ✅ SAFE
                "pixel_area": f["pixel_area"],
                "merge_count": f.get("merge_count"),
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(path, "w") as f:
        json.dump(geojson, f, indent=2)
