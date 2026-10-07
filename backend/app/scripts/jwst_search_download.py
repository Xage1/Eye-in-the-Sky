"""
app/scripts/jwst_search_download.py

Search the MAST archive for public JWST observations and download the
Stage 3 calibrated, rectified mosaic (_i2d.fits) product. Uses astroquery
to talk directly to the official MAST servers -- the same source NASA
and STScI scientists use. No API key needed for public data.

Usage:
    python -m app.scripts.jwst_search_download --proposal-id 2731 --instrument NIRCAM
    python -m app.scripts.jwst_search_download --target "Carina Nebula" --radius 0.2
"""

import argparse
from astroquery.mast import Observations


def search_by_target(target: str, radius_deg: float):
    print(f"Resolving '{target}' and searching JWST observations within {radius_deg} deg ...")
    return Observations.query_criteria(
        obs_collection="JWST",
        objectname=target,
        radius=f"{radius_deg} deg",
        dataproduct_type="image",
    )


def search_by_proposal(proposal_id: str, instrument: str = None):
    print(f"Searching JWST proposal {proposal_id} ...")
    criteria = dict(obs_collection="JWST", proposal_id=proposal_id, dataproduct_type="image")
    if instrument:
        criteria["instrument_name"] = instrument
    return Observations.query_criteria(**criteria)


def main():
    parser = argparse.ArgumentParser(description="Search and download JWST _i2d.fits mosaics from MAST")
    parser.add_argument("--target", help="Target name to resolve, e.g. 'Carina Nebula'")
    parser.add_argument("--radius", type=float, default=0.2, help="Search radius in degrees (used with --target)")
    parser.add_argument("--proposal-id", help="JWST proposal ID, e.g. 2731 for the Carina Nebula ERO image")
    parser.add_argument("--instrument", help="Filter by instrument, e.g. NIRCAM, MIRI")
    parser.add_argument("--download-dir", default="./jwst_data", help="Directory to download files into")
    parser.add_argument("--max-products", type=int, default=1, help="Max number of _i2d.fits files to download")
    args = parser.parse_args()

    if not args.target and not args.proposal_id:
        parser.error("Provide either --target or --proposal-id")

    obs_table = (
        search_by_proposal(args.proposal_id, args.instrument)
        if args.proposal_id
        else search_by_target(args.target, args.radius)
    )

    print(f"Found {len(obs_table)} observation(s).")
    if len(obs_table) == 0:
        print("No observations found. Try a different target, radius, or proposal ID.")
        return

    print("Fetching product list ...")
    products = Observations.get_product_list(obs_table)
    print(f"Total products available: {len(products)}")

    # Stage 3, calibrated, rectified mosaic -- the final science-ready image.
    filtered = Observations.filter_products(
        products,
        productSubGroupDescription="I2D",
        calib_level=3,
        extension="fits",
    )
    print(f"Matching _i2d.fits products: {len(filtered)}")

    if len(filtered) == 0:
        print(
            "No _i2d.fits products found for this search. The target may only have "
            "Stage 2 (_cal.fits) products public, or this proposal may not have "
            "Stage 3 mosaics released yet."
        )
        return

    if args.max_products:
        filtered = filtered[: args.max_products]

    print(f"Downloading {len(filtered)} file(s) to {args.download_dir} ...")
    manifest = Observations.download_products(filtered, download_dir=args.download_dir)
    print(manifest)


if __name__ == "__main__":
    main()
