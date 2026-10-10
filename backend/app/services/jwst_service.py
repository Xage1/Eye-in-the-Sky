"""
app/services/jwst_service.py

JWST (James Webb Space Telescope) data search, download, and
visualization via the MAST archive, using astroquery and astropy.
"""

import os
import logging

import numpy as np
from astroquery.mast import Observations
from astropy.io import fits
from astropy.visualization import ZScaleInterval, AsinhStretch, ImageNormalize

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

_KNOWN_INSTRUMENTS = ["nircam", "miri", "nirspec", "niriss", "fgs"]


def _guess_instrument(filename: str) -> str | None:
    lowered = filename.lower()
    for name in _KNOWN_INSTRUMENTS:
        if name in lowered:
            return name
    return None


def search_jwst_targets(target: str, radius_deg: float = 0.2, max_results: int = 20) -> list[dict]:
    """
    Free-text search for public JWST observations of a target
    (e.g. "Carina Nebula", "NGC 3324"), returning final Stage-3
    mosaic (I2D) products that are publicly downloadable right now.
    Proprietary/embargoed products (dataRights != PUBLIC) are excluded,
    since they would fail to download even though they show up in MAST.
    """
    obs_table = Observations.query_criteria(
        obs_collection="JWST",
        objectname=target,
        radius=f"{radius_deg} deg",
        dataproduct_type="image",
    )
    if len(obs_table) == 0:
        return []

    products = Observations.get_product_list(obs_table)
    filtered = Observations.filter_products(
        products,
        productSubGroupDescription="I2D",
        calib_level=3,
        extension="fits",
    )
    if len(filtered) == 0:
        return []

    cols = filtered.colnames
    if "dataRights" in cols:
        filtered = filtered[filtered["dataRights"] == "PUBLIC"]
    if len(filtered) == 0:
        return []

    results = []
    for row in filtered[:max_results]:
        filename = str(row["productFilename"])
        results.append({
            "product_uri": str(row["dataURI"]),
            "filename": filename,
            "obsid": str(row["obsID"]) if "obsID" in cols else None,
            "obs_id": str(row["obs_id"]) if "obs_id" in cols else None,
            "target_name": str(row["target_name"]) if "target_name" in cols else target,
            "instrument_name": _guess_instrument(filename),
            "proposal_id": str(row["proposal_id"]) if "proposal_id" in cols else None,
            "calib_level": int(row["calib_level"]) if "calib_level" in cols else None,
            "size_bytes": int(row["size"]) if "size" in cols else None,
        })
    return results


def download_and_process(obsid: str, filename: str, work_dir: str) -> dict:
    """
    Re-query MAST for the product list of a known numeric obsid, locate
    the exact file by name, download it via download_products, extract
    the SCI image, stretch it for visualization, and save a PNG preview.

    Mosaic images have gaps between detector/dither tiles (NaN pixels).
    Those are rendered as black (sky-black) rather than the default
    white figure background, so the gaps blend into the image instead
    of showing as a grid of white seams.

    Returns {"fits_path": ..., "preview_path": ...}
    """
    if not obsid:
        raise RuntimeError("obsid is required to download a JWST product")

    os.makedirs(work_dir, exist_ok=True)

    products = Observations.get_product_list(str(obsid))
    matches = products[products["productFilename"] == filename]
    if len(matches) == 0:
        raise RuntimeError(f"Product '{filename}' not found for obsid '{obsid}'")

    if "dataRights" in matches.colnames and str(matches["dataRights"][0]) != "PUBLIC":
        raise RuntimeError(
            f"Product '{filename}' is not public (dataRights={matches['dataRights'][0]}) "
            "-- it is still under a proprietary access hold and cannot be downloaded"
        )

    manifest = Observations.download_products(matches, download_dir=work_dir)

    if "Status" in manifest.colnames:
        status_val = str(manifest["Status"][0])
        if status_val != "COMPLETE":
            msg = str(manifest["Message"][0]) if "Message" in manifest.colnames else status_val
            raise RuntimeError(f"MAST download did not complete (status={status_val}): {msg}")

    local_path = str(manifest["Local Path"][0])
    if not os.path.isfile(local_path):
        raise RuntimeError(f"MAST reported success but file is missing on disk: {local_path}")

    with fits.open(local_path) as hdul:
        sci = hdul["SCI"].data

    sci = np.asarray(sci, dtype=float)
    mask = np.isfinite(sci)
    if not mask.any():
        raise RuntimeError("Downloaded FITS file has no finite pixel data in SCI extension")

    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(sci[mask])
    norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())

    cmap = plt.get_cmap("inferno").copy()
    cmap.set_bad(color="black")

    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.imshow(np.where(mask, sci, np.nan), cmap=cmap, origin="lower", norm=norm)
    ax.axis("off")

    preview_path = os.path.splitext(local_path)[0] + "_preview.png"
    fig.savefig(preview_path, bbox_inches="tight", pad_inches=0, facecolor="black")
    plt.close(fig)

    return {"fits_path": local_path, "preview_path": preview_path}
