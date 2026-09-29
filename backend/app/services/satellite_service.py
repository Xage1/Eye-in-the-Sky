"""
app/services/satellite_service.py

Fetches TLE data from Celestrak and computes which satellites are currently
visible above the observer's horizon using sgp4 + astropy.

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
"""

import time
from datetime import datetime

import httpx
import numpy as np
from sgp4.api import Satrec, SatrecArray, jday
from astropy.coordinates import EarthLocation, ITRS, TEME, AltAz
from astropy.time import Time
import astropy.units as u
import astropy.utils.iers as iers

# Do not depend on reaching IERS servers at request time. The bundled offline
# table is more than accurate enough for this use case.
iers.conf.auto_download = False
iers.conf.auto_max_age = None

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

_CACHE: dict = {"timestamp": 0, "data": []}
# Celestrak only refreshes the "active" group every 2 hours and returns 403
# if you re-request sooner. Cache TTL must be at or above that, or every
# request in the gap re-hits Celestrak, gets rejected, and falls back anyway.
_CACHE_TTL = 7200  # seconds


def fetch_tle_data() -> list[dict]:
    """
    Download and cache TLE data from Celestrak.
    Returns a list of dicts with keys: name, tle1, tle2.
    Cache TTL matches Celestrak's real update cadence to avoid
    guaranteed-failing refetches between updates.
    """
    now = time.time()
    if now - _CACHE["timestamp"] < _CACHE_TTL and _CACHE["data"]:
        return _CACHE["data"]

    try:
        with httpx.Client(timeout=20) as client:
            r = client.get(CELESTRAK_URL)
            r.raise_for_status()
            lines = r.text.strip().splitlines()

        sats = []
        for i in range(0, len(lines) - 2, 3):
            name = lines[i].strip()
            tle1 = lines[i + 1].strip()
            tle2 = lines[i + 2].strip()
            if tle1.startswith("1 ") and tle2.startswith("2 "):
                sats.append({"name": name, "tle1": tle1, "tle2": tle2})

        _CACHE["timestamp"] = now
        _CACHE["data"] = sats
        return sats

    except Exception as exc:
        # Return stale cache if fetch fails rather than crashing
        if _CACHE["data"]:
            return _CACHE["data"]
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
