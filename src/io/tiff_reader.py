# src/io/tiff_reader.py

import rasterio
from src.utils.logger import get_logger

logger = get_logger()

def open_tiff(path):
    if not path.exists():
        raise FileNotFoundError(f"TIFF not found: {path}")

    logger.info(f"Opening TIFF: {path}")
    ds = rasterio.open(path)
    logger.info(
        f"Opened TIFF | Size: {ds.width}x{ds.height} | Bands: {ds.count}"
    )
    return ds
