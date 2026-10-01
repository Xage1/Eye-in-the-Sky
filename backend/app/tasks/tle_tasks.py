"""
app/tasks/tle_tasks.py

Fetches fresh Two-Line Element sets from Celestrak and stores them in
Redis, shared with app.services.satellite_service so the API never has
to do a live Celestrak fetch during a request under normal operation.

Runs every 6 hours via Celery Beat.
"""

import json
import logging
import time

import httpx
from app.worker import celery_app
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

TLE_CACHE_KEY = "satellites:tle_cache"
TLE_CACHE_UPDATED_KEY = "satellites:tle_cache_updated_at"
# Safety-net expiry. Normal refresh is every 6h via Celery Beat; if Beat
# stops running for a long time, let the key expire rather than serve
# indefinitely-stale data forever.
TLE_CACHE_TTL_SECONDS = 24 * 3600


def _parse_tle_text(text: str) -> list[dict]:
    lines = text.strip().splitlines()
    sats = []
    for i in range(0, len(lines) - 2, 3):
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        if tle1.startswith("1 ") and tle2.startswith("2 "):
            sats.append({"name": name, "tle1": tle1, "tle2": tle2})
    return sats


@celery_app.task(
    name="app.tasks.tle_tasks.fetch_and_store_tle",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def fetch_and_store_tle(self):
    """
    Fetches the active satellite TLE catalogue from Celestrak and stores
    it in Redis for the API to read, avoiding a live fetch per request.
    """
    try:
        logger.info("TLE refresh: fetching from Celestrak ...")
        with httpx.Client(timeout=30) as client:
            resp = client.get(CELESTRAK_GP_URL)
            resp.raise_for_status()
            sats = _parse_tle_text(resp.text)

        if not sats:
            raise RuntimeError("TLE refresh: parsed 0 satellites, refusing to overwrite cache")

        r = get_redis_client()
        r.set(TLE_CACHE_KEY, json.dumps(sats), ex=TLE_CACHE_TTL_SECONDS)
        r.set(TLE_CACHE_UPDATED_KEY, str(time.time()), ex=TLE_CACHE_TTL_SECONDS)

        logger.info(f"TLE refresh: stored {len(sats)} satellites in Redis")
        return {"status": "ok", "satellites_fetched": len(sats)}

    except Exception as exc:
        logger.error(f"TLE refresh failed: {exc}")
        raise self.retry(exc=exc)
