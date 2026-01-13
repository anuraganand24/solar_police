

# ☀️ Solar Police — Solar Asset Inspection & Fault Detection Pipeline

## Overview

**Solar Police** is a modular, production-oriented computer vision pipeline for **automated inspection of utility-scale and rooftop solar installations** using high-resolution RGB and thermal imagery.

The system detects:

* Solar panel layouts
* Panel rows and geometry
* Thermal anomalies and fault patterns
* Asset-level outputs suitable for O&M, insurance, and performance analytics

The repository is designed with **engineering rigor**:

* Code-only versioning (no data committed)
* Clear modular boundaries
* Reproducible, testable pipeline stages
* Safe collaboration via Git branching and CI-ready structure

---

## Key Capabilities

### 🔍 Panel & Layout Detection

* Tile-based inference on very large geospatial rasters (TIFF)
* Robust handling of edge tiles and partial overlaps
* Geometry-aware grouping into rows and arrays

### 🌡️ Thermal Fault Analysis

* Thermal normalization and calibration
* Fault candidate detection and confidence scoring
* Priority classification for O&M triage

### 📐 Geometry & Metrics

* Panel orientation estimation
* Area, aspect ratio, centroid computation
* Row-level aggregation for plant-scale analysis

### 📤 Export & Visualization

* CSV and GeoJSON outputs for GIS tools
* Annotated image tiles for visual QA
* Structured logs for pipeline debugging

---

## Repository Structure

```text
solar_police/
│
├── src/                    # Core pipeline code
│   ├── io/                 # TIFF readers & tiling logic
│   ├── geometry/           # Panel, row, orientation logic
│   ├── thermal/            # Thermal normalization
│   ├── faults/             # Fault detection & scoring
│   ├── visualization/      # Annotation & overlays
│   ├── utils/              # Logging & helpers
│   └── main.py              # Pipeline entry point
│
├── data/                   # (Not versioned)
│   └── README.md            # Data expectations & usage
│
├── outputs/                # (Not versioned)
│   └── README.md            # Generated artifacts description
│
├── requirements.txt        # Python dependencies
├── .gitignore              # Strict data/output exclusion
└── README.md               # Project documentation
```

---

## Data Handling Philosophy

This repository **intentionally does not version data**.

Reasons:

* Imagery is large (GB-scale TIFFs)
* Data may be proprietary or sensitive
* Outputs are derived and reproducible

### Expected Local Structure

```text
data/
  raw/          # Input RGB / IR / thermal TIFFs
  processed/    # Intermediate artifacts
```

All data paths are configurable via `src/config.py`.

---

## How to Run

```bash
pip install -r requirements.txt
python src/main.py
```

Outputs will be generated automatically under:

```text
outputs/
```

---

## Engineering & Collaboration Practices

* **Branching**: GitHub Flow (`main`, `develop`, `feature/*`)
* **No data in Git**: enforced via `.gitignore`
* **Modular design**: each pipeline stage is independently testable
* **Baseline tagging**: semantic versioning for reproducibility

Baseline version:

```text
v1.0-baseline
```

---

## Intended Use Cases

* Solar O&M inspections
* Drone-based plant audits
* Thermal anomaly detection
* Insurance risk assessment
* Asset-level performance analytics
* CUF degradation studies (future roadmap)

---

## Roadmap

* Unit test coverage per module
* CI integration (GitHub Actions)
* Model versioning & evaluation harness
* Temporal degradation tracking
* Integration with GIS and asset management systems

---

## License & Usage

This repository is intended for **research, internal analytics, and controlled production use**.

Data, model weights, and site-specific configurations are expected to be supplied externally.

---
