import os
import cv2
import tifffile as tiff
import numpy as np
from tqdm import tqdm

TILE_SIZE = 1024
STRIDE = 1024

INPUT_TIFF = "data/raw/rgb.tif"
OUT_IMG_DIR = "data/tiles/images"
OUT_META_DIR = "data/tiles/metadata"

# Filtering thresholds (tuned for uint8 images)
MIN_MEAN_INTENSITY = 10     # too dark = useless
MIN_STD_INTENSITY = 5       # too flat = useless

os.makedirs(OUT_IMG_DIR, exist_ok=True)
os.makedirs(OUT_META_DIR, exist_ok=True)

img = tiff.imread(INPUT_TIFF)

# Drop alpha channel
if img.shape[2] == 4:
    img = img[:, :, :3]

H, W, _ = img.shape

tile_id = 0
kept = 0
skipped = 0

for y in tqdm(range(0, H - TILE_SIZE + 1, STRIDE)):
    for x in range(0, W - TILE_SIZE + 1, STRIDE):

        tile = img[y:y + TILE_SIZE, x:x + TILE_SIZE]

        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)

        mean_intensity = gray.mean()
        std_intensity = gray.std()

        # Skip black / empty tiles
        if mean_intensity < MIN_MEAN_INTENSITY or std_intensity < MIN_STD_INTENSITY:
            skipped += 1
            tile_id += 1
            continue

        tile_name = f"tile_{tile_id}.jpg"
        cv2.imwrite(os.path.join(OUT_IMG_DIR, tile_name), tile)

        meta = {
            "tile_id": tile_id,
            "x_offset": x,
            "y_offset": y,
            "height": TILE_SIZE,
            "width": TILE_SIZE,
            "mean": float(mean_intensity),
            "std": float(std_intensity)
        }

        np.save(
            os.path.join(OUT_META_DIR, f"tile_{tile_id}.npy"),
            meta
        )

        kept += 1
        tile_id += 1

print(f"Tiles kept   : {kept}")
print(f"Tiles skipped: {skipped}")
