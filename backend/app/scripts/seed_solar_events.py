"""
backend/app/scripts/seed_solar_events.py

Seeds the solar_events table with major celestial events for 2026.
Run inside Docker: docker-compose exec api python -m app.scripts.seed_solar_events
"""

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.solar_event import SolarEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


EVENTS = [
    # ── Eclipses ─────────────────────────────────────────────────────────────
    {"name": "Total Solar Eclipse", "event_type": "eclipse", "eclipse_type": "total", "start_time": dt("2026-08-12T17:00:00"), "end_time": dt("2026-08-12T20:00:00"), "peak_time": dt("2026-08-12T18:30:00"), "description": "Total solar eclipse visible across Greenland, Iceland, Spain, and northern Africa.", "visible_regions": "Greenland,Iceland,Spain,Algeria,Tunisia", "source": "NASA", "is_notable": True},
    {"name": "Annular Solar Eclipse", "event_type": "eclipse", "eclipse_type": "annular", "start_time": dt("2026-02-17T10:00:00"), "end_time": dt("2026-02-17T14:00:00"), "peak_time": dt("2026-02-17T12:00:00"), "description": "Annular solar eclipse visible from Antarctica and southern South America.", "visible_regions": "Antarctica,Argentina,Chile", "source": "NASA"},
    {"name": "Total Lunar Eclipse", "event_type": "eclipse", "eclipse_type": "total", "start_time": dt("2026-03-03T22:00:00"), "end_time": dt("2026-03-04T02:00:00"), "peak_time": dt("2026-03-04T00:00:00"), "description": "Total lunar eclipse visible across the Americas, Europe, and Africa.", "visible_regions": "Americas,Europe,Africa", "source": "NASA", "is_notable": True},
    # ── Meteor showers ───────────────────────────────────────────────────────
    {"name": "Quadrantids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-01-01T00:00:00"), "end_time": dt("2026-01-05T23:59:00"), "peak_time": dt("2026-01-03T12:00:00"), "description": "One of the best annual meteor showers, producing up to 120 multicolored meteors per hour.", "zhr": 120, "radiant_ra": 230.1, "radiant_dec": 48.5, "parent_body": "Asteroid 2003 EH1", "visible_regions": "Northern Hemisphere", "source": "AMS", "is_notable": True},
    {"name": "Lyrids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-04-16T00:00:00"), "end_time": dt("2026-04-25T23:59:00"), "peak_time": dt("2026-04-22T06:00:00"), "description": "Average shower producing about 20 meteors per hour at peak.", "zhr": 20, "radiant_ra": 271.4, "radiant_dec": 33.6, "parent_body": "Comet C/1861 G1 Thatcher", "visible_regions": "Northern Hemisphere", "source": "AMS"},
    {"name": "Eta Aquariids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-04-19T00:00:00"), "end_time": dt("2026-05-28T23:59:00"), "peak_time": dt("2026-05-06T03:00:00"), "description": "Debris from Halley's Comet — 30-40 meteors/hr, best from southern hemisphere.", "zhr": 40, "radiant_ra": 338.0, "radiant_dec": -1.0, "parent_body": "Halley's Comet", "visible_regions": "Southern Hemisphere,Tropics", "source": "AMS", "is_notable": True},
    {"name": "Perseids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-07-17T00:00:00"), "end_time": dt("2026-08-24T23:59:00"), "peak_time": dt("2026-08-12T22:00:00"), "description": "One of the most popular meteor showers — up to 100 multicolored meteors per hour.", "zhr": 100, "radiant_ra": 48.2, "radiant_dec": 58.1, "parent_body": "Comet 109P/Swift-Tuttle", "visible_regions": "Northern Hemisphere", "source": "AMS", "is_notable": True},
    {"name": "Orionids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-10-02T00:00:00"), "end_time": dt("2026-11-07T23:59:00"), "peak_time": dt("2026-10-21T10:00:00"), "description": "Debris from Halley's Comet — 20 meteors/hr, best after midnight.", "zhr": 20, "radiant_ra": 95.0, "radiant_dec": 16.0, "parent_body": "Halley's Comet", "visible_regions": "Worldwide", "source": "AMS"},
    {"name": "Leonids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-11-06T00:00:00"), "end_time": dt("2026-11-30T23:59:00"), "peak_time": dt("2026-11-17T14:00:00"), "description": "Fast meteors, up to 15 per hour at peak, occasional storm years.", "zhr": 15, "radiant_ra": 152.6, "radiant_dec": 22.0, "parent_body": "Comet 55P/Tempel-Tuttle", "visible_regions": "Worldwide", "source": "AMS"},
    {"name": "Geminids Meteor Shower", "event_type": "meteor_shower", "start_time": dt("2026-12-04T00:00:00"), "end_time": dt("2026-12-20T23:59:00"), "peak_time": dt("2026-12-14T02:00:00"), "description": "Best annual meteor shower — up to 120 multicolored meteors per hour.", "zhr": 120, "radiant_ra": 112.0, "radiant_dec": 32.5, "parent_body": "Asteroid 3200 Phaethon", "visible_regions": "Worldwide", "source": "AMS", "is_notable": True},
    # ── Planet conjunctions / oppositions ────────────────────────────────────
    {"name": "Mars at Opposition", "event_type": "opposition", "start_time": dt("2026-03-01T00:00:00"), "description": "Mars reaches opposition, its closest approach to Earth in 2026. Ideal viewing opportunity.", "visible_regions": "Worldwide", "source": "JPL", "is_notable": True},
    {"name": "Saturn at Opposition", "event_type": "opposition", "start_time": dt("2026-08-23T00:00:00"), "description": "Saturn at its closest and brightest for 2026, rings fully visible in binoculars.", "visible_regions": "Worldwide", "source": "JPL", "is_notable": True},
    {"name": "Jupiter at Opposition", "event_type": "opposition", "start_time": dt("2026-11-02T00:00:00"), "description": "Jupiter at opposition — largest and brightest appearance of the year.", "visible_regions": "Worldwide", "source": "JPL", "is_notable": True},
    {"name": "Venus at Greatest Brilliancy", "event_type": "conjunction", "start_time": dt("2026-02-20T00:00:00"), "description": "Venus reaches its greatest brilliancy as the evening star, magnitude -4.5.", "visible_regions": "Worldwide", "source": "JPL"},
    {"name": "ISS Visible Pass — East Africa", "event_type": "iss_pass", "start_time": dt("2026-04-01T19:45:00"), "end_time": dt("2026-04-01T19:51:00"), "description": "International Space Station visible pass over East Africa, max elevation 72°.", "visible_regions": "Kenya,Tanzania,Uganda,Ethiopia", "source": "NASA", "is_notable": True},
]


async def seed():
    async with SessionLocal() as db:
        result = await db.execute(select(SolarEvent).limit(1))
        if result.scalars().first():
            logger.info("Solar events already seeded — skipping")
            return

        for e in EVENTS:
            db.add(SolarEvent(
                name=e["name"],
                event_type=e["event_type"],
                description=e.get("description"),
                start_time=e["start_time"],
                end_time=e.get("end_time"),
                peak_time=e.get("peak_time"),
                visible_regions=e.get("visible_regions"),
                zhr=e.get("zhr"),
                radiant_ra=e.get("radiant_ra"),
                radiant_dec=e.get("radiant_dec"),
                parent_body=e.get("parent_body"),
                eclipse_type=e.get("eclipse_type"),
                magnitude=e.get("magnitude"),
                source=e.get("source"),
                is_notable=e.get("is_notable", False),
                is_upcoming=True,
            ))

        await db.commit()
        logger.info("Seeded %d solar events", len(EVENTS))


if __name__ == "__main__":
    asyncio.run(seed())