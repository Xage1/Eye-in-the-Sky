import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

RAW_FILE = DATA_DIR / "stars.json"
OUTPUT_FILE = DATA_DIR / "stars_catalogue.json"
FAMOUS_FILE = DATA_DIR / "famous_stars.json"

MIN_DEC = -60.0
MAX_DEC = 60.0


def dec_to_float(dec_str: str) -> float:
    """
    Convert DEC from '+DD:MM:SS' or '-DD:MM:SS' to float degrees
    """
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

    catalogue = {
        "metadata": {
            "catalog_name": "Unified Visible Star Catalogue",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epoch": "J2000",
            "visibility_rule": "-60° ≤ DEC ≤ +60°",
            "source": "Harvard Reference Catalogue"
        },
        "stars": []
    }

    for star in raw_stars:
        ra = star.get("RA")
        dec = star.get("DEC")

        if not ra or not dec:
            continue

        try:
            dec_value = dec_to_float(dec)
        except Exception:
            continue

        # 🌍 Hemisphere filter
        if not (MIN_DEC <= dec_value <= MAX_DEC):
            continue

        harvard_id = star.get("harvard_ref_#", None)
        magnitude = float(star.get("MAG", 99))

        # 🔎 Optional enrichment
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
                "name": enrichment["constellation"]["name"] if enrichment else None,
                "iau_abbreviation": enrichment["constellation"]["iau"] if enrichment else None
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

    print(f"✅ Catalogue built: {len(catalogue['stars'])} stars")


if __name__ == "__main__":
    build_catalogue()