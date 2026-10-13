"""
scripts/seed_solar_events.py

Seeds the solar_events table with:
  - well-known recurring meteor showers (next 2 occurrences from today)
  - confirmed solar/lunar eclipses for 2026-2027 (source: NASA / EclipseWise)

Only ever inserts events whose peak_time is still in the future relative
to when the script runs, and skips any (name, peak_time) pair that
already exists -- safe to re-run periodically (e.g. yearly) to roll the
meteor-shower horizon forward.

Usage (inside the API or worker container, where app/ is on PYTHONPATH):
    python scripts/seed_solar_events.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.sync_db import get_sync_session
from app.models.solar_event import SolarEvent


# name, month, day, zhr, radiant_ra, radiant_dec, parent_body, min_lat, max_lat
METEOR_SHOWERS = [
    ("Quadrantids",              1,  3, 120, 230.0,  49.0, "2003 EH1",            -20.0,  90.0),
    ("Lyrids",                   4, 22,  18, 271.0,  34.0, "Comet Thatcher",       -40.0,  90.0),
    ("Eta Aquariids",            5,  5,  50, 338.0,  -1.0, "Comet Halley",         -90.0,  60.0),
    ("Southern Delta Aquariids", 7, 30,  25, 339.0, -16.0, "96P/Machholz",         -90.0,  40.0),
    ("Perseids",                 8, 12, 100,  46.0,  58.0, "Comet Swift-Tuttle",   -20.0,  90.0),
    ("Orionids",                10, 21,  20,  95.0,  16.0, "Comet Halley",         -90.0,  90.0),
    ("Leonids",                 11, 17,  15, 152.0,  22.0, "Comet Tempel-Tuttle",  -90.0,  90.0),
    ("Geminids",                12, 13, 150, 112.0,  33.0, "3200 Phaethon",        -90.0,  90.0),
    ("Ursids",                  12, 22,  10, 217.0,  76.0, "Comet Tuttle",           0.0,  90.0),
]

# name, date, eclipse_type, event_type -- source: NASA / EclipseWise 2026-2027 canon
ECLIPSES = [
    ("Annular Solar Eclipse",   datetime(2026, 2, 17), "annular",   "solar_eclipse"),
    ("Total Lunar Eclipse",     datetime(2026, 3, 3),  "total",     "lunar_eclipse"),
    ("Total Solar Eclipse",     datetime(2026, 8, 12), "total",     "solar_eclipse"),
    ("Partial Lunar Eclipse",   datetime(2026, 8, 28), "partial",   "lunar_eclipse"),
    ("Annular Solar Eclipse",   datetime(2027, 2, 6),  "annular",   "solar_eclipse"),
    ("Penumbral Lunar Eclipse", datetime(2027, 2, 20), "penumbral", "lunar_eclipse"),
    ("Penumbral Lunar Eclipse", datetime(2027, 7, 18), "penumbral", "lunar_eclipse"),
    ("Total Solar Eclipse",     datetime(2027, 8, 2),  "total",     "solar_eclipse"),
    ("Penumbral Lunar Eclipse", datetime(2027, 8, 17), "penumbral", "lunar_eclipse"),
]


def _exists(db, name, peak_time):
    return (
        db.query(SolarEvent)
        .filter(SolarEvent.name == name, SolarEvent.peak_time == peak_time)
        .first()
        is not None
    )


def _next_occurrences(month, day, now, count=2):
    year = now.year
    first = datetime(year, month, day, 4, 0, 0)
    if first < now:
        first = datetime(year + 1, month, day, 4, 0, 0)
    return [datetime(first.year + i, month, day, 4, 0, 0) for i in range(count)]


def seed_meteor_showers(db, now):
    created = 0
    for name, month, day, zhr, ra, dec, parent, min_lat, max_lat in METEOR_SHOWERS:
        for peak in _next_occurrences(month, day, now):
            if _exists(db, name, peak):
                continue
            db.add(SolarEvent(
                name=name,
                event_type="meteor_shower",
                description=f"Annual meteor shower. Radiant near RA {ra} deg, Dec {dec} deg.",
                start_time=peak,
                peak_time=peak,
                min_latitude=min_lat,
                max_latitude=max_lat,
                zhr=zhr,
                radiant_ra=ra,
                radiant_dec=dec,
                parent_body=parent,
                source="seed_solar_events.py (recurring)",
                is_upcoming=True,
                is_notable=(zhr >= 100),
            ))
            created += 1
    return created


def seed_eclipses(db, now):
    created = 0
    for name, when, eclipse_type, event_type in ECLIPSES:
        if when < now:
            continue
        if _exists(db, name, when):
            continue
        db.add(SolarEvent(
            name=name,
            event_type=event_type,
            description=f"{name}. Visibility is a narrow path -- check NASA eclipse maps for your exact location.",
            start_time=when,
            peak_time=when,
            eclipse_type=eclipse_type,
            source="NASA / EclipseWise",
            is_upcoming=True,
            is_notable=True,
        ))
        created += 1
    return created


def main():
    db = get_sync_session()
    try:
        now = datetime.utcnow()
        meteor_count = seed_meteor_showers(db, now)
        eclipse_count = seed_eclipses(db, now)
        db.commit()
        print(f"Seeded {meteor_count} meteor shower occurrences and {eclipse_count} eclipses.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
