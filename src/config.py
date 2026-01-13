# src/config.py

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data directory
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# File discovery (supports .tif and .tiff)
def find_tiff(prefix: str) -> Path:
    for ext in [".tif", ".tiff", ".TIF", ".TIFF"]:
        candidate = DATA_DIR / f"{prefix}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No TIFF found for '{prefix}' in {DATA_DIR}"
    )

RGB_PATH = find_tiff("rgb")
IR_PATH = find_tiff("ir")

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEBUG_TILE_DIR = OUTPUT_DIR / "tiles_debug"
LOG_DIR = OUTPUT_DIR / "logs"

# Tile config
TILE_SIZE = 1024
OVERLAP = 64
DEBUG_TILE_LIMIT = 10
IR_BAND_INDEX = 1   # change to 2 or 3 after inspection
RGB_BAND_INDICES = [1, 2, 3]
LOG_LEVEL = "INFO"

# --- STEP-4: Fault detection thresholds ---

HOTSPOT_ZSCORE = 4.0          # cell anomaly threshold
SUBSTRING_MIN_PIXELS = 40     # elongated hotspot
PANEL_MIN_AREA_RATIO = 0.30   # ignore tiny panel tiles

# Output paths
FAULTS_CSV = "outputs/faults/faults.csv"
FAULTS_GEOJSON = "outputs/faults/faults.geojson"
