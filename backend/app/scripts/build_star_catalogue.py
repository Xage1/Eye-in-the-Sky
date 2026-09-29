import json
from pathlib import Path
from datetime import datetime, timezone

from astropy.coordinates import SkyCoord, get_constellation
import astropy.units as u

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

RAW_FILE = DATA_DIR / "stars.json"
OUTPUT_FILE = DATA_DIR / "stars_catalogue.json"
FAMOUS_FILE = DATA_DIR / "famous_stars.json"

MIN_DEC = -60.0
MAX_DEC = 60.0


def dec_to_float(dec_str: str) -> float:
    sign = -1 if dec_str.startswith("-") else 1
    dec_str = dec_str.replace("+", "").replace("-", "")
    d, m, s = map(float, dec_str.split(":"))
    return sign * (d + m / 60 + s / 3600)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_catalogue():
    raw_stars: list[dict] = load_json(RAW_FILE)
    famous: dict = load_json(FAMOUS_FILE)

    filtered = []
    for star in raw_stars:
        ra = star.get("RA")
        dec = star.get("DEC")
        if not ra or not dec:
            continue
        try:
            dec_value = dec_to_float(dec)
        except Exception:
            continue
        if not (MIN_DEC <= dec_value <= MAX_DEC):
            continue
        filtered.append(star)

    print(f"Filtered to {len(filtered)} stars within DEC range")

    ra_list = [s["RA"] for s in filtered]
    dec_list = [s["DEC"] for s in filtered]

    coords = SkyCoord(ra=ra_list, dec=dec_list, unit=(u.hourangle, u.deg), frame="icrs")
    const_short = get_constellation(coords, short_name=True)
    const_long = get_constellation(coords, short_name=False)

    catalogue = {
        "metadata": {
            "catalog_name": "Unified Visible Star Catalogue",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epoch": "J2000",
            "visibility_rule": "-60\u00b0 <= DEC <= +60\u00b0",
            "source": "Harvard Reference Catalogue",
            "constellation_source": "astropy.coordinates.get_constellation (IAU boundaries)"
        },
        "stars": []
    }

    for star, c_short, c_long in zip(filtered, const_short, const_long):
        ra = star.get("RA")
        dec = star.get("DEC")
        harvard_id = star.get("harvard_ref_#", None)
        magnitude = float(star.get("MAG", 99))

        enrichment = famous.get(str(harvard_id))

        entry = {
            "id": harvard_id,
            "catalog_ids": {
                "harvard_ref": harvard_id,
                "hd": None,
                "hip": None
            },
            "identifiers": {
                "common_name": enrichment["common_name"] if enrichment else None,
                "bayer_designation": enrichment["bayer_designation"] if enrichment else None,
                "flamsteed_number": None
            },
            "constellation": {
                "name": str(c_long),
                "iau_abbreviation": str(c_short)
            },
            "coordinates": {
                "ra": ra,
                "dec": dec,
                "epoch": "J2000"
            },
            "proper_motion": {
                "ra": float(star.get("RA PM", 0.0)),
                "dec": float(star.get("DEC PM", 0.0))
            },
            "photometry": {
                "visual_magnitude": magnitude,
                "absolute_magnitude": None
            },
            "spectral": {
                "class": star.get("Title HD")
            },
            "classification": {
                "object_type": "Star",
                "luminosity_class": (
                    star["Title HD"][-1] if star.get("Title HD") else None
                ),
                "variability": False
            },
            "visibility": {
                "naked_eye": magnitude <= 6.0
            }
        }

        catalogue["stars"].append(entry)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2)

    print(f"Catalogue built: {len(catalogue['stars'])} stars")

    named = sum(1 for s in catalogue["stars"] if s["identifiers"]["common_name"])
    print(f"Named stars: {named}")


if __name__ == "__main__":
    build_catalogue()
