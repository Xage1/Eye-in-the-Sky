"""
backend/app/scripts/generate_stars_flat.py

Converts the rich stars_catalogue.json into the flat stars.json format
used by the sky engine.

Input:
    backend/app/data/stars_catalogue.json

Output:
    backend/app/data/stars.json

The rich catalogue keeps RA/DEC in astronomical string form.

The flat catalogue converts them into decimal degrees for the
real-time sky engine.
"""

import json
import logging
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "app" / "data" / "stars_catalogue.json"
OUTPUT_FILE = BASE_DIR / "app" / "data" / "stars.json"

MAG_LIMIT = 6.5


def hms_to_deg(hms: str) -> float:
    """
    Convert HH:MM:SS.SS right ascension into decimal degrees.
    """

    parts = hms.strip().split(":")

    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])

    return (
        hours
        + minutes / 60.0
        + seconds / 3600.0
    ) * 15.0


def dms_to_deg(dms: str) -> float:
    """
    Convert ±DD:MM:SS.SS declination into decimal degrees.
    """

    value = dms.strip()

    sign = -1 if value.startswith("-") else 1

    parts = value.lstrip("+-").split(":")

    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])

    return sign * (
        degrees
        + minutes / 60.0
        + seconds / 3600.0
    )


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"stars_catalogue.json not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        catalogue = json.load(file)

    stars_raw = (
        catalogue["stars"]
        if isinstance(catalogue, dict)
        else catalogue
    )

    logger.info(
        "Loaded %d stars from catalogue",
        len(stars_raw),
    )

    output = []

    skipped = 0

    for star in stars_raw:

        try:
            magnitude = star.get(
                "photometry",
                {},
            ).get("visual_magnitude")

            if magnitude is None:
                skipped += 1
                continue

            magnitude = float(magnitude)

            if magnitude > MAG_LIMIT:
                skipped += 1
                continue

            coordinates = star.get(
                "coordinates",
                {},
            )

            ra_raw = coordinates.get("ra")
            dec_raw = coordinates.get("dec")

            if not ra_raw or not dec_raw:
                skipped += 1
                continue

            ra_deg = hms_to_deg(str(ra_raw))
            dec_deg = dms_to_deg(str(dec_raw))

            identifiers = star.get(
                "identifiers",
                {},
            )

            common_name = identifiers.get(
                "common_name"
            )

            # IMPORTANT:
            #
            # Only stars explicitly listed in famous_stars.json
            # receive proper names.
            #
            # Every other star is displayed as HR <number>.
            #
            star_id = star.get("id")

            display_name = (
                common_name
                if common_name
                else f"HR {star_id}"
            )

            constellation = star.get(
                "constellation",
                {},
            )

            constellation_name = (
                constellation.get("name")
                or "Unassigned"
            )

            iau_abbreviation = (
                constellation.get(
                    "iau_abbreviation"
                )
            )

            output.append(
                {
                    "id": star_id,

                    "name": display_name,

                    "proper_name": common_name,

                    "bayer": identifiers.get(
                        "bayer_designation"
                    ),

                    "constellation": constellation_name,

                    "iau": iau_abbreviation,

                    "ra": round(
                        ra_deg,
                        6,
                    ),

                    "dec": round(
                        dec_deg,
                        6,
                    ),

                    "mag": round(
                        magnitude,
                        2,
                    ),

                    "spectral": star.get(
                        "spectral",
                        {},
                    ).get("class"),

                    "naked_eye": star.get(
                        "visibility",
                        {},
                    ).get(
                        "naked_eye",
                        magnitude <= 6.0,
                    ),
                }
            )

        except Exception as exc:
            logger.warning(
                "Skipping star %s: %s",
                star.get("id"),
                exc,
            )

            skipped += 1

    # Brightest stars first.
    output.sort(
        key=lambda star: star["mag"]
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    logger.info("")
    logger.info("==============================================")
    logger.info("FLAT STAR CATALOGUE GENERATED")
    logger.info("==============================================")
    logger.info(
        "Input stars:              %d",
        len(stars_raw),
    )
    logger.info(
        "Stars included:           %d",
        len(output),
    )
    logger.info(
        "Stars skipped:            %d",
        skipped,
    )
    logger.info(
        "Magnitude limit:          %.1f",
        MAG_LIMIT,
    )
    logger.info(
        "Output:                   %s",
        OUTPUT_FILE,
    )
    logger.info("==============================================")


if __name__ == "__main__":
    main()