"""
app/services/satellite_service.py

Fetches TLE data from Celestrak and computes which satellites are currently
visible above the observer's horizon using sgp4 + astropy.

"""

import time
from datetime import datetime

import httpx
from sgp4.api import Satrec, jday
from astropy.coordinates import EarthLocation, ITRS, AltAz
from astropy.time import Time
import astropy.units as u

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

_CACHE: dict = {"timestamp": 0, "data": []}
_CACHE_TTL = 3600  # seconds — refresh TLE data every hour


def fetch_tle_data() -> list[dict]:
    """
    Download and cache TLE data from Celestrak.
    Returns a list of dicts with keys: name, tle1, tle2.
    Uses a 1-hour in-memory cache to avoid hammering Celestrak.
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
    Return satellites currently visible above the observer's horizon.

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
    observer = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=alt_m * u.m)
    time_astropy = Time(when)
    altaz_frame = AltAz(obstime=time_astropy, location=observer)

    visible = []

    for t in tle_data:
        try:
            sat = Satrec.twoline2rv(t["tle1"], t["tle2"])
            e, r, _ = sat.sgp4(jd, fr)
            if e != 0:
                continue

            sat_itrs = ITRS(
                x=r[0] * u.km,
                y=r[1] * u.km,
                z=r[2] * u.km,
                obstime=time_astropy,
            )
            sat_altaz = sat_itrs.transform_to(altaz_frame)

            if sat_altaz.alt.deg > 0:
                visible.append({
                    "name":         t["name"],
                    "altitude_deg": round(float(sat_altaz.alt.deg), 2),
                    "azimuth_deg":  round(float(sat_altaz.az.deg), 2),
                })

            if len(visible) >= limit:
                break

        except Exception:
            continue

    return visible