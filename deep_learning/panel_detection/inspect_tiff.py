import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt

def inspect_tiff(path, title):
    img = tiff.imread(path)
    print(f"{title}")
    print("Shape:", img.shape)
    print("Dtype:", img.dtype)
    print("Min / Max:", np.min(img), np.max(img))

    # Show a preview
    if img.ndim == 2:
        plt.imshow(img, cmap="inferno")
    else:
        plt.imshow(img[:, :, :3])
    plt.title(title)
    plt.axis("off")
    plt.show()

inspect_tiff("data/raw/IR.tif", "IR Image")
inspect_tiff("data/raw/rgb.tif", "RGB Image")
