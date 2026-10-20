"""backend/scripts/seed_missing_stars.py

The original seed read data/stars_catalogue.json, which stops at |dec| = 60 deg, so the polar
stars (Polaris, Acrux, Hadar, Dubhe ...) never reached the table. data/stars.json holds all
9,096 Harvard Revised entries; add the ones the table lacks. The constellation is computed
from the coordinates with astropy (official IAU boundaries). New rows are named 'HR <n>';
run seed_star_names afterwards to give the bright ones proper names.

Run:  docker exec eyesky_api python -m scripts.seed_missing_stars
"""
import json
import os
import re
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord, get_constellation
from sqlalchemy import create_engine, text

DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "stars.json"
RA_RE = re.compile(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$")
DEC_RE = re.compile(r"^[+-]\d{2}:\d{2}:\d{2}(\.\d+)?$")


def main():
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    recs = raw.get("stars", raw) if isinstance(raw, dict) else raw
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        have = {r[0] for r in conn.execute(text("SELECT catalog_id FROM stars"))}
        todo, skipped = [], 0
        for r in recs:
            try:
                hr = int(r["harvard_ref_#"])
                ra = str(r["RA"]).strip()
                dec = str(r["DEC"]).strip()
                mag = float(str(r["MAG"]).strip())
            except (KeyError, ValueError, TypeError):
                skipped += 1
                continue
            if hr in have:
                continue
            if not (RA_RE.match(ra) and DEC_RE.match(dec)):
                skipped += 1
                continue
            todo.append((hr, ra, dec, mag))

        if not todo:
            print("nothing to add (table already complete); skipped invalid records:", skipped)
            return

        coords = SkyCoord([t[1] for t in todo], [t[2] for t in todo], unit=(u.hourangle, u.deg))
        full = get_constellation(coords)
        short = get_constellation(coords, short_name=True)
        rows = [
            {"hr": t[0], "name": f"HR {t[0]}", "con": str(full[i]), "abbr": str(short[i]),
             "ra": t[1], "dec": t[2], "mag": t[3]}
            for i, t in enumerate(todo)
        ]
        conn.execute(text(
            'INSERT INTO stars (catalog_id, proper_name, bayer_designation, constellation, '
            'iau_abbreviation, ra, "dec", magnitude) '
            "VALUES (:hr, :name, NULL, :con, :abbr, :ra, :dec, :mag)"), rows)
        decs = coords.dec.deg
        print(f"inserted={len(rows)} skipped_invalid={skipped} dec range of new stars: {decs.min():.1f}..{decs.max():.1f}")
        print("sample:", [(r["name"], r["abbr"], r["mag"]) for r in rows[:5]])
    eng.dispose()


if __name__ == "__main__":
    main()