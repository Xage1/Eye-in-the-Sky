import json
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "app" /  "data" / "stars_catalogue.json"


def normalize(value: str) -> str:
    return value.lower().strip()


@lru_cache
def load_star_map() -> dict[str, dict]:
    """
    Returns:
    {
        "aldebaran": {...},
        "α tau": {...},
        "hr_1457": {...}
    }
    """
    with DATA_FILE.open("r", encoding="utf-8") as f:
        catalogue = json.load(f)

    star_map: dict[str, dict] = {}

    for star in catalogue["stars"]:
        identifiers = star.get("identifiers", {})
        common = identifiers.get("common_name")
        bayer = identifiers.get("bayer_designation")
        star_id = star["id"]

        entry = {
            "id": star_id,
            "proper_name": common or bayer or f"HR {star_id}",
            "constellation": star["constellation"]["name"],
            "iau_abbreviation": star["constellation"].get("iau_abbreviation"),
            "ra": star["coordinates"]["ra"],
            "dec": star["coordinates"]["dec"],
            "magnitude": star["photometry"]["visual_magnitude"],
        }

        if common:
            star_map[normalize(common)] = entry

        if bayer:
            star_map[normalize(bayer)] = entry

        star_map[f"hr_{star_id}"] = entry

    return star_map