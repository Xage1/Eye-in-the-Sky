"""
app/tasks/weather_tasks.py
Refreshes sky visibility scores from OpenWeather for active user locations.
Runs every 3 hours via Celery Beat.
"""

import logging
import os
import httpx
from app.worker import celery_app

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@celery_app.task(
    name="app.tasks.weather_tasks.refresh_visibility_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def refresh_visibility_scores(self):
    """
    For each distinct user location in the DB, fetches cloud cover
    and computes a visibility score (0–100) for stargazing.
    Score = 100 - cloud_cover_percent (simple proxy).
    Stub — full implementation once location service is wired to weather API.
    """
    try:
        logger.info("Weather refresh: updating visibility scores ...")
        # TODO: pull distinct locations from DB, batch-call OpenWeather,
        # write visibility_score back to location_entries
        return {"status": "ok", "locations_updated": 0}
    except Exception as exc:
        logger.error(f"Weather refresh failed: {exc}")
        raise self.retry(exc=exc)