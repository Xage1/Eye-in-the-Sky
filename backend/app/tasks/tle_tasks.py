"""
app/tasks/tle_tasks.py

Fetches fresh Two-Line Element sets from Celestrak and stores them in
Redis, shared with app.services.satellite_service so the API never has
to do a live Celestrak fetch during a request under normal operation.

Runs every 6 hours via Celery Beat.

Celestrak only republishes about every 2 hours and blocks clients that
download the same file repeatedly, so this task:
  * skips the download while the cached copy is still fresh,
  * never overwrites a good cache with a failure,
  * treats 403/429 as "try again much later" instead of a hard error.
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
# Safety-net expiry. Normal refresh is every 6h via Celery Beat; the long
# window lets a few blocked attempts pass without emptying the cache.
TLE_CACHE_TTL_SECONDS = 72 * 3600
# Do not re-download while the cache is younger than this.
MIN_REFRESH_AGE_SECONDS = 3 * 3600
BLOCKED_RETRY_SECONDS = 2 * 3600
USER_AGENT = "EyeSky/1.0 (satellite tracker)"


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


def _cache_age_seconds(r):
    try:
        raw = r.get(TLE_CACHE_UPDATED_KEY)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        return time.time() - float(raw)
    except Exception:
        return None


@celery_app.task(
    name="app.tasks.tle_tasks.fetch_and_store_tle",
    bind=True,
    max_retries=3,
    default_retry_delay=900,
)
def fetch_and_store_tle(self, force: bool = False):
    """
    Fetches the active satellite TLE catalogue from Celestrak and stores
    it in Redis for the API to read, avoiding a live fetch per request.
    """
    r = get_redis_client()
    age = _cache_age_seconds(r)
    if not force and age is not None and age < MIN_REFRESH_AGE_SECONDS and r.exists(TLE_CACHE_KEY):
        logger.info(f"TLE refresh: cache is {age / 60:.0f} min old, skipping download")
        return {"status": "skipped", "cache_age_seconds": int(age)}

    try:
        logger.info("TLE refresh: fetching from Celestrak ...")
        with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
            resp = client.get(CELESTRAK_GP_URL)
            resp.raise_for_status()
            sats = _parse_tle_text(resp.text)

        if not sats:
            raise RuntimeError("TLE refresh: parsed 0 satellites, refusing to overwrite cache")

        r.set(TLE_CACHE_KEY, json.dumps(sats), ex=TLE_CACHE_TTL_SECONDS)
        r.set(TLE_CACHE_UPDATED_KEY, str(time.time()), ex=TLE_CACHE_TTL_SECONDS)

        logger.info(f"TLE refresh: stored {len(sats)} satellites in Redis")
        return {"status": "ok", "satellites_fetched": len(sats)}

    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code in (403, 429):
            have_cache = bool(r.exists(TLE_CACHE_KEY))
            logger.warning(
                f"TLE refresh: Celestrak returned {code} (rate limited). "
                f"Keeping existing cache={have_cache}; retrying later."
            )
            if self.request.retries >= self.max_retries:
                return {"status": "blocked", "code": code, "cache_kept": have_cache}
            raise self.retry(exc=exc, countdown=BLOCKED_RETRY_SECONDS)
        logger.error(f"TLE refresh failed: {exc}")
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.error(f"TLE refresh failed: {exc}")
        raise self.retry(exc=exc)