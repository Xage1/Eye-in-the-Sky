import requests
import time
from datetime import datetime
from sgp4.api import Satrec, jday
from astropy.coordinates import EarthLocation, ITRS, AltAz, CartesianRepresentation
from astropy.time import Time
import astropy.units as u

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/active.txt"
_CACHE = {"timestamp": 0, "data": []}
_CACHE_TTL = 3600  # seconds


def fetch_tle_data():
    """Download and cache TLE data from CelesTrak."""
    now = time.time()
    if now - _CACHE["timestamp"] < _CACHE_TTL and _CACHE["data"]:
        return _CACHE["data"]

    r = requests.get(CELESTRAK_URL, timeout=20)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    sats = []
    for i in range(0, len(lines) - 2, 3):
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        sats.append({"name": name, "tle1": tle1, "tle2": tle2})

    _CACHE["timestamp"] = now
    _CACHE["data"] = sats
    return sats


def get_visible_satellites(lat, lon, alt_m=0.0, when=None, limit=10):
    """Return a list of satellites visible above horizon at given location/time."""
    when = when or datetime.utcnow()
    jd, fr = jday(when.year, when.month, when.day, when.hour, when.minute, when.second + when.microsecond * 1e-6)
    tle_data = fetch_tle_data()
    observer = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=alt_m * u.m)
    time_astropy = Time(when)
    visible = []

    for t in tle_data:
        try:
            sat = Satrec.twoline2rv(t["tle1"], t["tle2"])
            e, r, v = sat.sgp4(jd, fr)
            if e != 0:
                continue

            sat_itrs = ITRS(
                x=r[0] * u.km, y=r[1] * u.km, z=r[2] * u.km,
                obstime=time_astropy
            )
            sat_altaz = sat_itrs.transform_to(AltAz(obstime=time_astropy, location=observer))

            if sat_altaz.alt.deg > 0:
                visible.append({
                    "name": t["name"],
                    "altitude_deg": round(sat_altaz.alt.deg, 2),
                    "azimuth_deg": round(sat_altaz.az.deg, 2),
                })

            if len(visible) >= limit:
                break
        except Exception:
            continue
    return visible