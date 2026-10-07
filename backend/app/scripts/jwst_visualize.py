"""
app/scripts/jwst_visualize.py

Open a JWST Stage 3 _i2d.fits mosaic, extract the science image data,
apply a stretch so faint nebular detail is visible, and plot it.

Usage:
    python -m app.scripts.jwst_visualize path/to/file_i2d.fits --output out.png
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ZScaleInterval, AsinhStretch, ImageNormalize


def load_science_data(fits_path: str) -> np.ndarray:
    with fits.open(fits_path) as hdul:
        hdul.info()
        # The science image lives in the 'SCI' extension, not the primary
        # HDU -- HDU 0 is normally just header metadata with no pixel data.
        sci = hdul["SCI"].data
    return sci


def main():
    parser = argparse.ArgumentParser(description="Visualize a JWST _i2d.fits mosaic")
    parser.add_argument("fits_path", help="Path to the _i2d.fits file")
    parser.add_argument("--output", default="jwst_preview.png", help="Output PNG path")
    parser.add_argument("--cmap", default="inferno", help="Matplotlib colormap")
    args = parser.parse_args()

    data = load_science_data(args.fits_path)
    print(f"Image shape: {data.shape}, dtype: {data.dtype}")

    # NaNs are common in mosaics (unexposed or rectification gaps) -- mask
    # them out of the stretch calculation so they do not skew the scaling.
    finite = np.isfinite(data)
    print(f"Finite pixels: {finite.sum()} / {data.size}")

    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(data[finite])
    norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())

    plt.figure(figsize=(10, 10))
    plt.imshow(data, origin="lower", cmap=args.cmap, norm=norm)
    plt.colorbar(label="Flux (calibrated)")
    plt.title(args.fits_path.split("/")[-1].split("\\")[-1])
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
