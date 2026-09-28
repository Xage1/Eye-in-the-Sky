import json
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "app"
    / "data"
    / "stars_catalogue.json"
)


def normalize(value: str) -> str:
    return value.lower().strip()


@lru_cache
def load_star_map() -> dict[str, dict]:
    """
    Load the unified star catalogue into a lookup map.

    Supported lookups include:

        sirius
        rigel
        betelgeuse
        hr_2491
        hr_1713
        hr_2061

    Bayer designations are also retained as lookup aliases,
    but they never replace the HR fallback display name.
    """

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        catalogue = json.load(file)

    star_map: dict[str, dict] = {}

    for star in catalogue["stars"]:

        identifiers = star.get(
            "identifiers",
            {},
        )

        common_name = identifiers.get(
            "common_name"
        )

        bayer_designation = identifiers.get(
            "bayer_designation"
        )

        star_id = star["id"]

        # Only famous stars have common names.
        # All other stars use HR <number>.
        proper_name = (
            common_name
            if common_name
            else f"HR {star_id}"
        )

        constellation = star.get(
            "constellation",
            {},
        )

        entry = {
            "id": star_id,

            "proper_name": proper_name,

            "bayer_designation": (
                bayer_designation
            ),

            "constellation": (
                constellation.get("name")
                or "Unassigned"
            ),

            "iau_abbreviation": (
                constellation.get(
                    "iau_abbreviation"
                )
            ),

            "ra": star[
                "coordinates"
            ]["ra"],

            "dec": star[
                "coordinates"
            ]["dec"],

            "magnitude": star[
                "photometry"
            ]["visual_magnitude"],
        }

        # ---------------------------------------------------------
        # Common-name lookup
        # ---------------------------------------------------------

        if common_name:
            star_map[
                normalize(common_name)
            ] = entry

        # ---------------------------------------------------------
        # Bayer lookup
        #
        # This remains a search alias, not the proper/display name.
        # ---------------------------------------------------------

        if bayer_designation:
            star_map[
                normalize(bayer_designation)
            ] = entry

        # ---------------------------------------------------------
        # Harvard Reference lookup
        # ---------------------------------------------------------

        star_map[
            f"hr_{star_id}"
        ] = entry

    return star_map