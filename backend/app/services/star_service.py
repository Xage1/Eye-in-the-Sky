"""
app/services/star_service.py

Star lookups backed by the `stars` table (HR catalogue loaded by seed_stars).
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

import astropy.units as u
from astropy.coordinates import SkyCoord
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def _constellations() -> dict:
    with (_DATA_DIR / "constellations.json").open("r", encoding="utf-8") as f:
        return json.load(f)


_SQL = text("""
    SELECT id, catalog_id, proper_name, bayer_designation, constellation,
           iau_abbreviation, ra, "dec", magnitude
    FROM stars
    WHERE lower(proper_name) = :q
       OR lower(bayer_designation) = :q
       OR 'hr ' || CAST(catalog_id AS TEXT) = :q
       OR CAST(catalog_id AS TEXT) = :q
    ORDER BY magnitude
    LIMIT 1
""")


async def get_star_detail_db(db: AsyncSession, star_name: str) -> Optional[dict]:
    """Match on proper name, Bayer designation, or HR number (case-insensitive)."""
    q = star_name.strip().lower()
    if not q:
        return None
    row = (await db.execute(_SQL, {"q": q})).mappings().first()
    if row is None:
        return None

    star = dict(row)
    try:
        c = SkyCoord(star["ra"], star["dec"], unit=(u.hourangle, u.deg))
        star["ra_deg"] = round(float(c.ra.deg), 5)
        star["dec_deg"] = round(float(c.dec.deg), 5)
    except Exception:
        pass

    info = _constellations().get(star.get("constellation") or "", {})
    star["constellation_detail"] = {
        "name": star.get("constellation"),
        "description": info.get("description"),
        "myth": info.get("myth"),
        "discoverer": info.get("discoverer"),
        "year": info.get("year"),
        "brightest_star": info.get("brightest_star"),
    }
    return star