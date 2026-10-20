"""app/services/constellation_service.py - constellations above the horizon, computed with astropy."""
import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_constellation
from astropy.time import Time
from astropy.utils import iers

try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "ignore"
except Exception:
    pass

_DATA = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def _lore() -> dict:
    with (_DATA / "constellations.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def evening_time(lat_lon_lon: float, date_str: Optional[str]) -> datetime:
    """20:00 local mean solar time on date_str, as an aware UTC datetime."""
    day = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now(timezone.utc).replace(tzinfo=None)
    base = datetime(day.year, day.month, day.day, 20, 0)
    return (base - timedelta(hours=lat_lon_lon / 15.0)).replace(tzinfo=timezone.utc)


def visible_constellations(lat: float, lon: float, when: Optional[datetime] = None) -> dict:
    when = when or datetime.now(timezone.utc)
    t = Time(when.astimezone(timezone.utc).replace(tzinfo=None), scale="utc")
    loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)

    az = np.arange(0.0, 360.0, 10.0)
    alt = np.arange(5.0, 90.0, 10.0)
    A, H = np.meshgrid(az, alt)
    A, H = A.ravel(), H.ravel()
    coords = SkyCoord(az=A * u.deg, alt=H * u.deg, frame=AltAz(obstime=t, location=loc)).icrs
    names = np.asarray(get_constellation(coords))

    lore = _lore()
    result = []
    for name in sorted(set(names.tolist())):
        m = names == name
        a = np.deg2rad(A[m])
        mean_az = float(np.rad2deg(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) % 360.0)
        info = lore.get(name, {})
        result.append({
            "name": name,
            "sky_share_pct": round(100.0 * float(m.sum()) / len(names), 1),
            "approx_azimuth_deg": round(mean_az, 0),
            "mean_altitude_deg": round(float(H[m].mean()), 0),
            "description": info.get("description"),
            "myth": info.get("myth"),
            "brightest_star": info.get("brightest_star"),
        })
    result.sort(key=lambda r: r["sky_share_pct"], reverse=True)
    return {"time_utc": t.utc.datetime.strftime("%Y-%m-%dT%H:%M:%SZ"), "constellations": result}