"""
backend/app/scripts/generate_stars_flat.py

Converts the rich stars_catalogue.json into the flat stars.json format
that skyController.py reads every frame.

stars_catalogue.json has RA/Dec as "HH:MM:SS.SS" strings.
skyController.py needs RA/Dec as decimal degrees.

Output: backend/app/data/stars.json

Run: docker-compose exec api python -m app.scripts.generate_stars_flat
  or: python -m app.scripts.generate_stars_flat  (from backend/)
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR     = Path(__file__).resolve().parents[2]
INPUT_FILE   = BASE_DIR / "app" / "data" / "stars_catalogue.json"
OUTPUT_FILE  = BASE_DIR / "app" / "data" / "stars.json"
FAMOUS_FILE  = BASE_DIR / "app" / "data" / "famous_stars.json"

MAG_LIMIT = 6.5  # only include stars visible to naked eye or binoculars


def hms_to_deg(hms: str) -> float:
    """Convert HH:MM:SS.SS right ascension string to decimal degrees."""
    parts = hms.strip().split(":")
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return (h + m / 60.0 + s / 3600.0) * 15.0


def dms_to_deg(dms: str) -> float:
    """Convert ±DD:MM:SS.SS declination string to decimal degrees."""
    sign = -1 if dms.strip().startswith("-") else 1
    parts = dms.strip().lstrip("+-").split(":")
    d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return sign * (d + m / 60.0 + s / 3600.0)


def load_famous_names() -> dict[int, dict]:
    """Load famous star names keyed by Harvard Ref catalog ID."""
    if not FAMOUS_FILE.exists():
        return {}
    with FAMOUS_FILE.open() as f:
        data = json.load(f)
    # Rebuild as {lower_name: info} for lookup
    return data if isinstance(data, dict) else {}


def main():
    if not INPUT_FILE.exists():
        logger.error("stars_catalogue.json not found at %s", INPUT_FILE)
        logger.error("Run the build_star_catalogue.py script first.")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        catalogue = json.load(f)

    stars_raw = catalogue.get("stars", catalogue) if isinstance(catalogue, dict) else catalogue
    logger.info("Loaded %d stars from catalogue", len(stars_raw))

    output = []
    skipped = 0

    for star in stars_raw:
        try:
            # Magnitude filter
            mag = star.get("photometry", {}).get("visual_magnitude")
            if mag is None or float(mag) > MAG_LIMIT:
                skipped += 1
                continue

            # Convert coordinates
            coords = star.get("coordinates", {})
            ra_raw  = coords.get("ra",  "0:0:0")
            dec_raw = coords.get("dec", "0:0:0")

            try:
                ra_deg  = hms_to_deg(str(ra_raw))
                dec_deg = dms_to_deg(str(dec_raw))
            except Exception:
                skipped += 1
                continue

            # Names
            idents   = star.get("identifiers", {})
            common   = idents.get("common_name")
            bayer    = idents.get("bayer_designation")
            const    = star.get("constellation", {})
            const_name = const.get("name") or ""

            name = common or bayer or f"HR {star.get('id', '')}"

            output.append({
                "id":            star.get("id"),
                "name":          name,
                "proper_name":   common,
                "bayer":         bayer,
                "constellation": const_name,
                "iau":           const.get("iau_abbreviation"),
                "ra":            round(ra_deg, 6),
                "dec":           round(dec_deg, 6),
                "mag":           round(float(mag), 2),
                "spectral":      star.get("spectral", {}).get("class"),
                "naked_eye":     star.get("visibility", {}).get("naked_eye", mag <= 6.0),
            })

        except Exception as exc:
            logger.debug("Skipping star %s: %s", star.get("id"), exc)
            skipped += 1
            continue

    # Sort by magnitude — brightest first (most important for AR)
    output.sort(key=lambda s: s["mag"])

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(
        "Generated stars.json: %d stars included, %d skipped (mag > %.1f)",
        len(output), skipped, MAG_LIMIT,
    )
    logger.info("Output: %s", OUTPUT_FILE)


if __name__ == "__main__":
    main()