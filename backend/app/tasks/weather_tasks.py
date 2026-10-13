"""
app/tasks/weather_tasks.py

Refreshes cached stargazing visibility scores for every saved user
location. Runs every 3 hours via Celery Beat (see app/worker.py).

Reuses the scoring logic already live behind GET /skyinfo/visibility
(app.controllers.skyController.get_sky_visibility) rather than
duplicating the OpenWeather call here. Locations are deduplicated by
rounding to 2 decimal places (about 1.1km) so users clustered in the
same area only cost one API call per refresh cycle.
"""

import asyncio
import logging
from datetime import datetime

from app.worker import celery_app
from app.utils.sync_db import get_sync_session
from app.models.location import Location
from app.controllers.skyController import get_sky_visibility

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.weather_tasks.refresh_visibility_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def refresh_visibility_scores(self):
    db = get_sync_session()
    try:
        locations = db.query(Location).all()
        if not locations:
            logger.info("Weather refresh: no saved locations to update")
            return {"status": "ok", "locations_updated": 0}

        buckets = {}
        for loc in locations:
            key = (round(loc.latitude, 2), round(loc.longitude, 2))
            buckets.setdefault(key, []).append(loc)

        updated = 0
        failed = 0
        now = datetime.utcnow()

        for (lat, lon), rows in buckets.items():
            try:
                result = asyncio.run(get_sky_visibility(lat, lon))
            except Exception as exc:
                logger.warning("Visibility fetch failed for (%s, %s): %s", lat, lon, exc)
                failed += 1
                continue

            if "error" in result:
                logger.warning("Visibility fetch error for (%s, %s): %s", lat, lon, result["error"])
                failed += 1
                continue

            score = result["visibility_score"]
            for row in rows:
                row.visibility_score = score
                row.visibility_updated_at = now
                updated += 1

        db.commit()
        logger.info(
            "Weather refresh: %s locations updated across %s distinct spots, %s spots failed",
            updated, len(buckets), failed,
        )
        return {"status": "ok", "locations_updated": updated, "spots_failed": failed}
    except Exception as exc:
        db.rollback()
        logger.error(f"Weather refresh failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
