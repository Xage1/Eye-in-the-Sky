"""
app/utils/satellite_tools.py

Lower-level satellite visibility utilities using sgp4 + astropy.

"""

from datetime import datetime

import httpx
from sgp4.api import Satrec
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, ITRS, CartesianRepresentation
import astropy.units as u

TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"


def fetch_tle_data() -> list[dict]:
    """Fetch active TLE data from Celestrak. Returns list of {name, satrec} dicts."""
    with httpx.Client(timeout=20) as client:
        response = client.get(TLE_URL)
        response.raise_for_status()
        lines = response.text.strip().splitlines()

    satellites = []
    for i in range(0, len(lines) - 2, 3):
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        if not (tle1.startswith("1 ") and tle2.startswith("2 ")):
            continue
        try:
            satrec = Satrec.twoline2rv(tle1, tle2)
            satellites.append({"name": name, "satrec": satrec})
        except Exception:
            continue
    return satellites


def is_satellite_visible(satrec, observer: EarthLocation, time_utc: datetime) -> dict | None:
    """
    Check if a satellite is above the horizon at the observer's location.
    Returns {azimuth, elevation} if visible, else None.
    """
    t = Time(time_utc)
    from sgp4.api import jday
    jd, fr = jday(
        time_utc.year, time_utc.month, time_utc.day,
        time_utc.hour, time_utc.minute,
        time_utc.second + time_utc.microsecond * 1e-6,
    )
    error_code, position, _ = satrec.sgp4(jd, fr)
    if error_code != 0:
        return None

    sat_cartesian = CartesianRepresentation(
        position[0] * u.km,
        position[1] * u.km,
        position[2] * u.km,
    )
    itrs = ITRS(sat_cartesian, obstime=t)
    altaz = itrs.transform_to(AltAz(obstime=t, location=observer))

    if altaz.alt.deg > 0:
        return {
            "azimuth":   round(float(altaz.az.deg), 2),
            "elevation": round(float(altaz.alt.deg), 2),
        }
    return None


def get_visible_satellites(
    lat: float,
    lon: float,
    alt_m: float = 0,
    when: datetime = None,
    max_results: int = 10,
) -> list[dict]:
    """Get visible satellites from observer location at a given UTC time."""
    time_utc = when or datetime.utcnow()
    observer = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=alt_m * u.m)
    tle_data = fetch_tle_data()
    visible = []

    for sat in tle_data:
        visibility = is_satellite_visible(sat["satrec"], observer, time_utc)
        if visibility:
            visible.append({
                "name":      sat["name"],
                "azimuth":   visibility["azimuth"],
                "elevation": visibility["elevation"],
            })
            if len(visible) >= max_results:
                break

    return visible