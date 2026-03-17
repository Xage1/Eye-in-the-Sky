"""
app/tasks/tle_tasks.py
Fetches fresh Two-Line Element sets from Celestrak and stores them in the DB.
Runs every 6 hours via Celery Beat.
"""

import logging
import httpx
from app.worker import celery_app

logger = logging.getLogger(__name__)

CELESTRAK_URLS = {
    "stations":    "https://celestrak.org/SOCRATES/query.php",
    "active":      "https://celestrak.org/SOCRATES/query.php",
    "visual":      "https://celestrak.org/SOCRATES/query.php",
    # Full GP catalog (TLE format)
    "gp_active":   "https://celestrak.org/SOCRATES/query.php",
}

CELESTRAK_GP_URL = (
    "https://celestrak.org/SOCRATES/query.php"
    "?GROUP=active&FORMAT=tle"
)


@celery_app.task(
    name="app.tasks.tle_tasks.fetch_and_store_tle",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def fetch_and_store_tle(self):
    """
    Fetches the active satellite TLE catalog from Celestrak
    and upserts into the satellites table.
    """
    try:
        logger.info("TLE refresh: fetching from Celestrak ...")
        # TODO: replace stub with real DB upsert once satellite model is ready
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                "https://celestrak.org/SOCRATES/query.php",
                params={"GROUP": "active", "FORMAT": "tle"},
            )
            resp.raise_for_status()
            lines = resp.text.strip().splitlines()
            count = len(lines) // 3
            logger.info(f"TLE refresh: received {count} satellite records")
            # Stub — actual DB write goes here
            return {"status": "ok", "satellites_fetched": count}

    except Exception as exc:
        logger.error(f"TLE refresh failed: {exc}")
        raise self.retry(exc=exc)