import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord, get_constellation


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

RAW_FILE = DATA_DIR / "stars.json"
OUTPUT_FILE = DATA_DIR / "stars_catalogue.json"
FAMOUS_FILE = DATA_DIR / "famous_stars.json"

MIN_DEC = -60.0
MAX_DEC = 60.0


def dec_to_float(dec_str: str) -> float:
    """
    Convert DEC from '+DD:MM:SS' or '-DD:MM:SS'
    into decimal degrees.
    """

    value = dec_str.strip()

    sign = -1 if value.startswith("-") else 1

    value = value.lstrip("+-")

    degrees, minutes, seconds = map(float, value.split(":"))

    return sign * (
        degrees
        + minutes / 60.0
        + seconds / 3600.0
    )


def load_json(path: Path):
    """
    Load UTF-8 JSON while preserving Unicode characters.
    """

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_constellation(
    ra: str,
    dec: str,
) -> tuple[str, str]:
    """
    Determine the IAU constellation from J2000 RA/DEC.

    Returns:
        (
            full_constellation_name,
            IAU_three_letter_abbreviation
        )
    """

    try:
        coordinate = SkyCoord(
            ra=ra,
            dec=dec,
            unit=(u.hourangle, u.deg),
            frame="icrs",
        )

        constellation_name = get_constellation(
            coordinate,
            short_name=False,
        )

        constellation_abbreviation = get_constellation(
            coordinate,
            short_name=True,
        )

        return (
            constellation_name,
            constellation_abbreviation,
        )

    except Exception as exc:
        logger.warning(
            "Could not determine constellation for RA=%s DEC=%s: %s",
            ra,
            dec,
            exc,
        )

        return (
            "Unassigned",
            None,
        )


def build_catalogue():
    """
    Build the rich unified star catalogue.

    Pipeline:

        raw stars.json
            ↓
        DEC visibility filter
            ↓
        HR-number famous-star lookup
            ↓
        Astropy constellation calculation
            ↓
        stars_catalogue.json
    """

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw star catalogue not found: {RAW_FILE}"
        )

    if not FAMOUS_FILE.exists():
        raise FileNotFoundError(
            f"Famous star catalogue not found: {FAMOUS_FILE}"
        )

    raw_stars = load_json(RAW_FILE)
    famous = load_json(FAMOUS_FILE)

    if not isinstance(raw_stars, list):
        raise ValueError(
            "stars.json must contain a JSON list of raw Harvard star records."
        )

    if not isinstance(famous, dict):
        raise ValueError(
            "famous_stars.json must contain an object keyed by HR number."
        )

    catalogue = {
        "metadata": {
            "catalog_name": "Unified Visible Star Catalogue",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "epoch": "J2000",
            "visibility_rule": "-60° ≤ DEC ≤ +60°",
            "source": "Harvard Reference Catalogue",
            "constellation_source": "Astropy IAU constellation boundaries",
        },
        "stars": [],
    }

    skipped_missing_coordinates = 0
    skipped_invalid_dec = 0
    skipped_outside_visibility = 0
    constellation_failures = 0
    famous_matches = 0

    for star in raw_stars:

        ra = star.get("RA")
        dec = star.get("DEC")

        if not ra or not dec:
            skipped_missing_coordinates += 1
            continue

        try:
            dec_value = dec_to_float(dec)
        except Exception:
            skipped_invalid_dec += 1
            continue

        # Keep the existing project visibility rule.
        if not (MIN_DEC <= dec_value <= MAX_DEC):
            skipped_outside_visibility += 1
            continue

        harvard_id = star.get("harvard_ref_#")

        if harvard_id is None:
            logger.warning(
                "Star has no Harvard Reference number: %s",
                star,
            )
            continue

        try:
            harvard_id = int(harvard_id)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid Harvard Reference number: %r",
                harvard_id,
            )
            continue

        try:
            magnitude = float(star.get("MAG", 99))
        except (TypeError, ValueError):
            magnitude = 99.0

        # ---------------------------------------------------------
        # Famous-star lookup
        #
        # IMPORTANT:
        # famous_stars.json is keyed by HR number.
        # ---------------------------------------------------------

        enrichment = famous.get(str(harvard_id))

        if enrichment:
            famous_matches += 1

            common_name = enrichment.get("common_name")
            bayer_designation = enrichment.get("bayer_designation")
        else:
            common_name = None
            bayer_designation = None

        # ---------------------------------------------------------
        # Constellation calculation
        #
        # This is deliberately calculated for EVERY star.
        # The famous-star metadata does not determine constellation.
        # ---------------------------------------------------------

        constellation_name, constellation_abbreviation = (
            calculate_constellation(
                ra=ra,
                dec=dec,
            )
        )

        if constellation_name == "Unassigned":
            constellation_failures += 1

        entry = {
            "id": harvard_id,

            "catalog_ids": {
                "harvard_ref": harvard_id,
                "hd": None,
                "hip": None,
            },

            "identifiers": {
                "common_name": common_name,
                "bayer_designation": bayer_designation,
                "flamsteed_number": None,
            },

            "constellation": {
                "name": constellation_name,
                "iau_abbreviation": constellation_abbreviation,
            },

            "coordinates": {
                "ra": ra,
                "dec": dec,
                "epoch": "J2000",
            },

            "proper_motion": {
                "ra": float(star.get("RA PM", 0.0)),
                "dec": float(star.get("DEC PM", 0.0)),
            },

            "photometry": {
                "visual_magnitude": magnitude,
                "absolute_magnitude": None,
            },

            "spectral": {
                "class": star.get("Title HD"),
            },

            "classification": {
                "object_type": "Star",
                "luminosity_class": (
                    star["Title HD"][-1]
                    if star.get("Title HD")
                    else None
                ),
                "variability": False,
            },

            "visibility": {
                "naked_eye": magnitude <= 6.0,
            },
        }

        catalogue["stars"].append(entry)

    # -------------------------------------------------------------
    # Write catalogue
    # -------------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            catalogue,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    # -------------------------------------------------------------
    # Validation summary
    # -------------------------------------------------------------

    total = len(catalogue["stars"])

    logger.info("")
    logger.info("==============================================")
    logger.info("STAR CATALOGUE BUILD COMPLETE")
    logger.info("==============================================")
    logger.info("Raw Harvard records:       %d", len(raw_stars))
    logger.info("Catalogue records:         %d", total)
    logger.info("Famous-star matches:       %d", famous_matches)
    logger.info("Constellation failures:    %d", constellation_failures)
    logger.info(
        "Missing coordinates:       %d",
        skipped_missing_coordinates,
    )
    logger.info(
        "Invalid DEC:               %d",
        skipped_invalid_dec,
    )
    logger.info(
        "Outside DEC range:         %d",
        skipped_outside_visibility,
    )
    logger.info("Output: %s", OUTPUT_FILE)
    logger.info("==============================================")


if __name__ == "__main__":
    build_catalogue()