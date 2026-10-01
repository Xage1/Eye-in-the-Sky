"""
app/services/satellite_service.py

Computes which satellites are currently visible above the observer's
horizon using sgp4 + astropy. TLE data is read from Redis, where
app.tasks.tle_tasks.fetch_and_store_tle keeps it refreshed every 6
hours. If Redis has no data yet (fresh environment, Beat hasn't run),
this falls back to a live Celestrak fetch and writes the result into
Redis itself, so the feature works even before the first scheduled run.

Notes on correctness and performance (fixed after profiling):

- SGP4 output is in the TEME frame (True Equator, Mean Equinox), not ITRS.
  It must be converted TEME -> ITRS -> AltAz. Treating raw SGP4 output as
  ITRS directly produces errors of tens of degrees in altitude/azimuth.

- IERS auto-download is disabled. Sub-arcsecond Earth-orientation precision
  is not needed for naked-eye satellite visibility, and depending on an
  external IERS server at request time adds latency and a failure mode.

- All satellites are propagated and transformed in a single batched call
  (SatrecArray + one astropy transform) rather than one at a time. A single
  coordinate transform has several seconds of fixed one-time setup cost per
  process, but transforming thousands of points in one call afterward costs
  well under a second. Looping per-satellite pays that fixed cost every time.

- TLE data lives in Redis (shared with the Celery worker) rather than an
  in-process dict, so it survives API restarts and both processes agree
  on the same data.
"""

import json
import time
from datetime import datetime

import httpx
import numpy as np
from sgp4.api import Satrec, SatrecArray, jday
from astropy.coordinates import EarthLocation, ITRS, TEME, AltAz
from astropy.time import Time
import astropy.units as u
import astropy.utils.iers as iers

from app.utils.redis_client import get_redis_client

# Do not depend on reaching IERS servers at request time. The bundled offline
# table is more than accurate enough for this use case.
iers.conf.auto_download = False
iers.conf.auto_max_age = None

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

TLE_CACHE_KEY = "satellites:tle_cache"
TLE_CACHE_UPDATED_KEY = "satellites:tle_cache_updated_at"
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


def fetch_tle_data() -> list[dict]:
    """
    Return TLE data, preferring the Redis cache that the Celery task
    keeps refreshed. Falls back to a live Celestrak fetch (and writes
    the result into Redis) if Redis has nothing yet.
    """
    r = get_redis_client()

    try:
        cached = r.get(TLE_CACHE_KEY)
        if cached:
            return json.loads(cached)
    except Exception:
        # Redis unreachable: fall through to a live fetch rather than fail outright.
        pass

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(CELESTRAK_URL)
            resp.raise_for_status()
            sats = _parse_tle_text(resp.text)

        if sats:
            try:
                r.set(TLE_CACHE_KEY, json.dumps(sats), ex=TLE_CACHE_TTL_SECONDS)
                r.set(TLE_CACHE_UPDATED_KEY, str(time.time()), ex=TLE_CACHE_TTL_SECONDS)
            except Exception:
                pass

        return sats

    except Exception as exc:
        raise RuntimeError(f"TLE fetch failed and no cache available: {exc}") from exc


def get_visible_satellites(
    lat: float,
    lon: float,
    alt_m: float = 0.0,
    when: datetime = None,
    limit: int = 10,
) -> list[dict]:
    """
    Return satellites currently visible above the observer's horizon,
    sorted by altitude (highest / most overhead first).

    Parameters
    ----------
    lat, lon : observer coordinates in decimal degrees
    alt_m    : observer altitude in metres above sea level
    when     : UTC datetime (defaults to now)
    limit    : max number of results to return

    Returns
    -------
    List of dicts with: name, altitude_deg, azimuth_deg
    """
    when = when or datetime.utcnow()

    jd, fr = jday(
        when.year, when.month, when.day,
        when.hour, when.minute,
        when.second + when.microsecond * 1e-6,
    )

    tle_data = fetch_tle_data()
    if not tle_data:
        return []

    sat_objs = []
    valid_tle = []
    for t in tle_data:
        try:
            sat_objs.append(Satrec.twoline2rv(t["tle1"], t["tle2"]))
            valid_tle.append(t)
        except Exception:
            continue

    if not sat_objs:
        return []

    sat_array = SatrecArray(sat_objs)
    jd_arr = np.array([jd])
    fr_arr = np.array([fr])
    e_arr, r_arr, _ = sat_array.sgp4(jd_arr, fr_arr)

    e_flat = e_arr[:, 0]
    ok_mask = e_flat == 0

    x = r_arr[:, 0, 0]
    y = r_arr[:, 0, 1]
    z = r_arr[:, 0, 2]

    observer = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=alt_m * u.m)
    time_astropy = Time(when)
    altaz_frame = AltAz(obstime=time_astropy, location=observer)

    teme = TEME(
        x=x * u.km, y=y * u.km, z=z * u.km,
        representation_type="cartesian",
        obstime=time_astropy,
    )
    altaz = teme.transform_to(ITRS(obstime=time_astropy)).transform_to(altaz_frame)

    alt_deg = altaz.alt.deg
    az_deg = altaz.az.deg

    results = []
    for i, t in enumerate(valid_tle):
        if not ok_mask[i]:
            continue
        if alt_deg[i] > 0:
            results.append({
                "name": t["name"],
                "altitude_deg": round(float(alt_deg[i]), 2),
                "azimuth_deg": round(float(az_deg[i]), 2),
            })

    results.sort(key=lambda s: s["altitude_deg"], reverse=True)
    return results[:limit]
