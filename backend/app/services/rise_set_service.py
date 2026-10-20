"""
app/services/rise_set_service.py

Rise / transit / set times for the Sun, Moon and planets, computed locally with
astropy's built-in ephemeris (no API key, no network).

Speed: the expensive part (ephemeris + precession) is location-independent, so it
is evaluated once per UTC date on a 30-minute grid and cached. Each request is then
pure numpy: interpolate to a 2-minute grid, sidereal-time trigonometry, find crossings.

The search window is the observer's local mean solar day for the requested date:
24 h starting at local mean midnight (00:00 UTC minus longitude/15 h).
All returned times are UTC, ISO 8601.
"""
import calendar
import math
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

import astropy.units as u
import numpy as np
from astropy.coordinates import FK5, SkyCoord, get_body, solar_system_ephemeris
from astropy.time import Time
from astropy.utils import iers

from app.services.scene_fast import _equatorial_to_horizontal, _gmst_deg

try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "ignore"
except Exception:
    pass

_BODIES = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune")
_H0 = {"sun": -0.833, "moon": -0.833}  # upper limb + refraction (moon: topocentric centre)
_PLANET_H0 = -0.567                    # refraction only
_STEP_S = 120
_COARSE_S = 1800
_NC = 97                               # 48 h of 30-min samples: covers every possible window
_FMT = "%Y-%m-%dT%H:%M:%SZ"
_A_KM = 6378.137

_cache: dict = {}
_lock = threading.Lock()


def _ephemeris(day):
    with _lock:
        hit = _cache.get(day)
        if hit is not None:
            return hit
        t0 = calendar.timegm(datetime(day.year, day.month, day.day).timetuple()) - 12 * 3600
        grid = t0 + np.arange(_NC) * _COARSE_S
        times = Time(grid, format="unix", scale="utc")
        mid = Time(float(grid[_NC // 2]), format="unix", scale="utc")
        data = {}
        with solar_system_ephemeris.set("builtin"):
            for name in _BODIES:
                c = get_body(name, times)  # geocentric GCRS: ra/dec = direction from Earth's centre
                p = SkyCoord(np.asarray(c.ra.deg) * u.deg, np.asarray(c.dec.deg) * u.deg,
                             frame="icrs").transform_to(FK5(equinox=mid))  # equinox of date
                ra = np.rad2deg(np.unwrap(np.deg2rad(np.asarray(p.ra.deg))))
                data[name] = (ra, np.asarray(p.dec.deg), np.asarray(c.distance.to_value(u.km)))
        if len(_cache) > 6:
            _cache.clear()
        _cache[day] = (grid, data)
        return _cache[day]


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(_FMT)


def _crossing(t, s, rising):
    if rising:
        idx = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0))
    else:
        idx = np.flatnonzero((s[:-1] >= 0) & (s[1:] < 0))
    if idx.size == 0:
        return None
    i = int(idx[0])
    frac = float(-s[i] / (s[i + 1] - s[i]))  # linear interpolation between samples
    return float(t[i] + frac * (t[i + 1] - t[i]))


def _transit(t, alt):
    k = int(np.argmax(alt))
    if k == 0 or k == len(alt) - 1:
        return None  # culmination falls outside this window
    a, b, c = alt[k - 1], alt[k], alt[k + 1]
    denom = a - 2 * b + c
    offset = 0.5 * (a - c) / denom if denom != 0 else 0.0
    return float(t[k] + offset * (t[k + 1] - t[k]))


def _body_events(t, alt, h0):
    s = alt - h0
    rise = _crossing(t, s, True)
    set_ = _crossing(t, s, False)
    transit = _transit(t, alt)
    if rise is None and set_ is None:
        status = "always_up" if float(s.min()) >= 0 else "never_up"
    else:
        status = "ok"
    return {
        "rise": _iso(rise) if rise is not None else None,
        "transit": _iso(transit) if transit is not None else None,
        "set": _iso(set_) if set_ is not None else None,
        "status": status,
        "max_altitude_deg": round(float(alt.max()), 2),
    }


def get_rise_set(lat: float, lon: float, when: Optional[datetime] = None) -> dict:
    when = when or datetime.now(timezone.utc)
    day = when.astimezone(timezone.utc).date() if when.tzinfo else when.date()
    start = datetime(day.year, day.month, day.day) - timedelta(hours=lon / 15.0)  # naive, UTC
    start_ts = start.replace(tzinfo=timezone.utc).timestamp()

    grid, eph = _ephemeris(day)
    n = 24 * 3600 // _STEP_S + 1
    t = start_ts + np.arange(n) * _STEP_S
    lst = _gmst_deg(t / 86400.0 + 2440587.5) + lon

    bodies = {}
    for name in _BODIES:
        ra_c, dec_c, dist_c = eph[name]
        ra = np.interp(t, grid, ra_c) % 360.0
        dec = np.interp(t, grid, dec_c)
        alt, _ = _equatorial_to_horizontal(ra, dec, lst, lat)
        if name == "moon":
            dist = np.interp(t, grid, dist_c)
            alt = alt - np.rad2deg(np.arcsin(_A_KM / dist)) * np.cos(np.deg2rad(alt))  # parallax
        bodies[name] = _body_events(t, alt, _H0.get(name, _PLANET_H0))

    return {
        "window_start_utc": start.strftime(_FMT),
        "window_end_utc": (start + timedelta(hours=24)).strftime(_FMT),
        "bodies": bodies,
    }