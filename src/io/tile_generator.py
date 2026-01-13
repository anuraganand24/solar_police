# src/io/tile_generator.py

from rasterio.windows import Window
from rasterio.windows import transform as window_transform
import numpy as np

from src.config import TILE_SIZE, OVERLAP
from src.utils.logger import get_logger

logger = get_logger()


def generate_tiles(dataset, band_index=None, band_indices=None):
    """
    Memory-safe tile generator with geospatial transform support.

    Parameters
    ----------
    band_index : int
        Read a single band (IR use-case)
    band_indices : list[int]
        Read multiple specific bands (RGB use-case)

    Yields
    ------
    dict with keys:
        tile       : np.ndarray
        window     : rasterio.windows.Window
        transform  : affine.Affine (tile-level geotransform)
        x, y       : pixel offsets
        bands      : number of bands
    """

    width, height = dataset.width, dataset.height
    step = TILE_SIZE - OVERLAP

    logger.info(
        f"Generating tiles | step={step} | "
        f"band_index={band_index} | band_indices={band_indices}"
    )

    for y in range(0, height, step):
        for x in range(0, width, step):

            win = Window(
                col_off=x,
                row_off=y,
                width=min(TILE_SIZE, width - x),
                height=min(TILE_SIZE, height - y),
            )

            # ---- Single band (IR) ----
            if band_index is not None:
                tile = dataset.read(
                    band_index,
                    window=win,
                    masked=True
                ).filled(0)

                # (H, W) → (H, W, 1)
                tile = tile[:, :, None]

            # ---- Multi-band (RGB) ----
            elif band_indices is not None:
                bands = []
                for b in band_indices:
                    band = dataset.read(
                        b,
                        window=win,
                        masked=True
                    ).filled(0)
                    bands.append(band)

                # (bands, H, W) → (H, W, bands)
                tile = np.stack(bands, axis=-1)

            # ---- All bands fallback ----
            else:
                tile = dataset.read(
                    window=win,
                    masked=True
                ).filled(0)

                tile = np.moveaxis(tile, 0, -1)

            # 🔑 IMPORTANT: compute tile-level transform
            tile_transform = window_transform(win, dataset.transform)

            yield {
                "tile": tile,
                "window": win,
                "transform": tile_transform,
                "x": x,
                "y": y,
                "bands": tile.shape[-1],
            }
