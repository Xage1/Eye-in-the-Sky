"""
app/services/scene_fast.py

Fast replacements for the per-frame AR scene functions in skyController.

Why: the originals cost ~1 s each for planets / satellites, made an HTTP call to
Open Notify for the ISS on every frame, and the star function silently returned
nothing because catalogue RA/Dec are sexagesimal strings.

Approach
  * Stars     : catalogue loaded once from the `stars` table (names included). RA/Dec are
                precessed to the equinox of date once per day with astropy; each frame is
                then plain sidereal-time trigonometry in numpy (~1 ms).
  * Planets   : astropy built-in ephemeris evaluated once per 30-min block on a 5-min grid
                (3 h span) and interpolated; the next block is prefetched in a thread.
                Moon gets a topocentric parallax correction.
  * Satellites: local TLEs through sgp4, TEME -> ECEF by GMST rotation, ECEF -> topocentric
                by geometry. No astropy frame transforms, no network.
  * ISS       : same sgp4 path (needs an "ISS ..." entry in the TLE catalogue).
"""
from __future__ import annotations

import logging
import math
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import astropy.units as u
import numpy as np
from astropy.coordinates import FK5, SkyCoord, get_body, solar_system_ephemeris
from astropy.time import Time
from astropy.utils import iers

try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "ignore"
except Exception:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)

_CATALOGUE_MAG_MAX = 6.5
_BODIES = ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "moon", "sun")
_A_KM = 6378.137
_F = 1.0 / 298.257223563
_E2 = _F * (2.0 - _F)


# ───────────────────────────── time / geometry helpers ─────────────────────────────

def _utc(when: Optional[datetime]) -> datetime:
    if when is None:
        return datetime.now(timezone.utc)
    return when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when.astimezone(timezone.utc)


def _jd(when: datetime) -> float:
    return when.timestamp() / 86400.0 + 2440587.5


def _gmst_deg(jd_ut1: float) -> float:
    """Greenwich mean sidereal time in degrees (IAU 1982), UT1 taken as UTC."""
    T = (jd_ut1 - 2451545.0) / 36525.0
    sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + 0.093104 * T * T - 6.2e-6 * T ** 3
    return (sec % 86400.0) / 240.0


def _equatorial_to_horizontal(ra_deg, dec_deg, lst_deg, lat_deg):
    """RA/Dec of date -> (alt, az) degrees. Az from North through East."""
    H = np.deg2rad(lst_deg - np.asarray(ra_deg))
    dec = np.deg2rad(np.asarray(dec_deg))
    phi = math.radians(lat_deg)
    sin_alt = np.sin(dec) * math.sin(phi) + np.cos(dec) * math.cos(phi) * np.cos(H)
    alt = np.arcsin(np.clip(sin_alt, -1.0, 1.0))
    az = np.arctan2(-np.cos(dec) * np.sin(H),
                    np.sin(dec) * math.cos(phi) - np.cos(dec) * math.sin(phi) * np.cos(H))
    return np.rad2deg(alt), np.rad2deg(az) % 360.0


def _unit(alt_deg, az_deg):
    a, z = np.deg2rad(alt_deg), np.deg2rad(az_deg)
    ca = np.cos(a)
    return np.stack([ca * np.sin(z), ca * np.cos(z), np.sin(a)], axis=-1)  # E, N, U


def _project_many(alt, az, device_az, device_alt, device_roll, fov_h, fov_v, w, h):
    """Vectorised twin of skyController._altaz_to_screen. Returns (x, y, angle_deg, keep)."""
    target = _unit(alt, az)
    fwd = _unit(device_alt, device_az)
    dot = np.clip(target @ fwd, -1.0, 1.0)

    right = np.cross(fwd, [0.0, 0.0, 1.0])
    rn = np.linalg.norm(right)
    right = right / rn if rn >= 1e-6 else np.array([1.0, 0.0, 0.0])
    cam_up = np.cross(right, fwd)
    r = math.radians(device_roll)
    right_r = math.cos(r) * right + math.sin(r) * cam_up
    up_r = -math.sin(r) * right + math.cos(r) * cam_up

    offset = target - dot[:, None] * fwd
    on = np.linalg.norm(offset, axis=1)
    safe = np.where(on < 1e-9, 1.0, on)
    ou = offset / safe[:, None]
    ang = np.arccos(dot)
    ax = ang * (ou @ right_r)
    ay = ang * (ou @ up_r)
    ax = np.where(on < 1e-9, 0.0, ax)
    ay = np.where(on < 1e-9, 0.0, ay)

    px = w / 2.0 + ax / math.radians(fov_h / 2.0) * (w / 2.0)
    py = h / 2.0 - ay / math.radians(fov_v / 2.0) * (h / 2.0)
    m = 50
    keep = (dot >= 0) & (px >= -m) & (px <= w + m) & (py >= -m) & (py <= h + m)
    return np.round(px, 1), np.round(py, 1), np.rad2deg(ang), keep


# ───────────────────────────── stars ─────────────────────────────

_cat_lock = threading.Lock()
_cat: Optional[dict] = None
_of_date: dict = {}  # {"day": ordinal, "ra": array, "dec": array}


def _sync_db_url() -> str:
    url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
    return url.replace("+asyncpg", "")


def _load_catalogue() -> Optional[dict]:
    global _cat
    if _cat is not None:
        return _cat
    with _cat_lock:
        if _cat is not None:
            return _cat
        try:
            from sqlalchemy import create_engine, text
            eng = create_engine(_sync_db_url(), pool_pre_ping=True)
            with eng.connect() as conn:
                rows = conn.execute(text(
                    'SELECT catalog_id, proper_name, bayer_designation, constellation, ra, "dec", magnitude '
                    "FROM stars WHERE magnitude IS NOT NULL AND magnitude <= :m"), {"m": _CATALOGUE_MAG_MAX}).all()
            eng.dispose()
            if not rows:
                logger.warning("scene_fast: stars table is empty")
                return None
            c = SkyCoord([r[4] for r in rows], [r[5] for r in rows], unit=(u.hourangle, u.deg))
            _cat = {
                "hr": [r[0] for r in rows],
                "name": [r[1] for r in rows],
                "bayer": [r[2] for r in rows],
                "constellation": [r[3] for r in rows],
                "mag": np.array([float(r[6]) for r in rows]),
                "ra": np.asarray(c.ra.deg), "dec": np.asarray(c.dec.deg),
            }
            logger.info("scene_fast: loaded %d stars", len(rows))
        except Exception as exc:
            logger.warning("scene_fast: star catalogue load failed: %s", exc)
            return None
        return _cat


def _stars_of_date(cat: dict, when: datetime):
    day = when.toordinal()
    if _of_date.get("day") != day:
        t = Time(datetime(when.year, when.month, when.day, 12), scale="utc")
        c = SkyCoord(cat["ra"] * u.deg, cat["dec"] * u.deg, frame="icrs").transform_to(FK5(equinox=t))
        _of_date.update(day=day, ra=np.asarray(c.ra.deg), dec=np.asarray(c.dec.deg))
    return _of_date["ra"], _of_date["dec"]


def get_visible_stars(lat, lon, when, device_az, device_alt, device_roll, screen_w, screen_h,
                      fov_h: float = 60.0, fov_v: float = 110.0, mag_limit: float = 5.5) -> list:
    cat = _load_catalogue()
    if cat is None:
        return []
    when = _utc(when)
    ra, dec = _stars_of_date(cat, when)
    lst = _gmst_deg(_jd(when)) + lon
    alt, az = _equatorial_to_horizontal(ra, dec, lst, lat)

    idx = np.flatnonzero((alt >= 0.0) & (cat["mag"] <= mag_limit))
    if idx.size == 0:
        return []
    px, py, ang, keep = _project_many(alt[idx], az[idx], device_az, device_alt, device_roll,
                                      fov_h, fov_v, screen_w, screen_h)
    out = []
    for k in np.flatnonzero(keep):
        i = int(idx[k])
        out.append({
            "name": cat["name"][i] or f"HR {cat['hr'][i]}",
            "hr": cat["hr"][i],
            "bayer": cat["bayer"][i],
            "constellation": cat["constellation"][i] or "",
            "magnitude": round(float(cat["mag"][i]), 2),
            "ra": round(float(cat["ra"][i]), 4),
            "dec": round(float(cat["dec"][i]), 4),
            "altitude_deg": round(float(alt[i]), 2),
            "azimuth_deg": round(float(az[i]), 2),
            "screen_x": float(px[k]),
            "screen_y": float(py[k]),
            "distance_from_centre_deg": round(float(ang[k]), 2),
        })
    out.sort(key=lambda s: s["magnitude"])
    return out


# ───────────────────────────── planets ─────────────────────────────

_BLOCK_S = 1800
_STEP_S = 300
_N = 37  # 3 h
_series: dict = {}
_inflight: set = set()
_series_lock = threading.Lock()


def _compute_block(block: int) -> dict:
    with _series_lock:
        if block in _series:
            return _series[block]
        t0 = block * _BLOCK_S
        times = Time(t0 + np.arange(_N) * _STEP_S, format="unix", scale="utc")
        data = {}
        with solar_system_ephemeris.set("builtin"):
            for name in _BODIES:
                c = get_body(name, times)  # geocentric GCRS: ra/dec = direction seen from Earth centre
                data[name] = (
                    np.rad2deg(np.unwrap(np.deg2rad(np.asarray(c.ra.deg)))),
                    np.asarray(c.dec.deg),
                    np.asarray(c.distance.to_value(u.km)),
                )
        if len(_series) > 12:
            _series.clear()
        _series[block] = data
        return data


def _prefetch(block: int) -> None:
    if block in _series or block in _inflight:
        return
    _inflight.add(block)

    def run():
        try:
            _compute_block(block)
        except Exception as exc:  # pragma: no cover
            logger.warning("planet prefetch failed: %s", exc)
        finally:
            _inflight.discard(block)

    threading.Thread(target=run, daemon=True).start()


def get_planet_positions(lat, lon, when, device_az, device_alt, device_roll, screen_w, screen_h,
                         fov_h: float = 60.0, fov_v: float = 110.0) -> list:
    when = _utc(when)
    ts = when.timestamp()
    block = int(ts // _BLOCK_S)
    data = _series.get(block) or _compute_block(block)
    frac = (ts - block * _BLOCK_S) / _STEP_S
    grid = np.arange(_N)

    ra = np.array([np.interp(frac, grid, data[n][0]) for n in _BODIES]) % 360.0
    dec = np.array([np.interp(frac, grid, data[n][1]) for n in _BODIES])
    dist = np.array([np.interp(frac, grid, data[n][2]) for n in _BODIES])

    t = Time(ts, format="unix", scale="utc")
    c = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs").transform_to(FK5(equinox=t))
    alt, az = _equatorial_to_horizontal(np.asarray(c.ra.deg), np.asarray(c.dec.deg),
                                        _gmst_deg(_jd(when)) + lon, lat)
    mi = _BODIES.index("moon")
    par = math.degrees(math.asin(_A_KM / dist[mi]))
    alt[mi] -= par * math.cos(math.radians(alt[mi]))  # topocentric parallax

    px, py, _, keep = _project_many(np.clip(alt, -89.9, 90), az, device_az, device_alt, device_roll,
                                    fov_h, fov_v, screen_w, screen_h)
    out = []
    for i, name in enumerate(_BODIES):
        if alt[i] < 0:
            continue
        out.append({
            "name": name.capitalize(),
            "altitude_deg": round(float(alt[i]), 2),
            "azimuth_deg": round(float(az[i]), 2),
            "screen_x": float(px[i]) if keep[i] else None,
            "screen_y": float(py[i]) if keep[i] else None,
            "ra_deg": round(float(ra[i]) % 360.0, 4),
            "dec_deg": round(float(dec[i]), 4),
        })
    _prefetch(block + 1)
    return out


# ───────────────────────────── satellites / ISS ─────────────────────────────

_SAT_TTL = 600.0
_sat_cache: dict = {"t": 0.0, "names": [], "arr": None}
_sat_lock = threading.Lock()


def _sat_catalogue():
    now = time.time()
    if _sat_cache["arr"] is not None and now - _sat_cache["t"] < _SAT_TTL:
        return _sat_cache["names"], _sat_cache["arr"]
    with _sat_lock:
        if _sat_cache["arr"] is not None and time.time() - _sat_cache["t"] < _SAT_TTL:
            return _sat_cache["names"], _sat_cache["arr"]
        from sgp4.api import Satrec, SatrecArray
        from app.services import satellite_service as ss
        names, objs = [], []
        for t in ss.fetch_tle_data() or []:
            try:
                objs.append(Satrec.twoline2rv(t["tle1"], t["tle2"]))
                names.append(t["name"])
            except Exception:
                continue
        _sat_cache["names"] = names
        _sat_cache["arr"] = SatrecArray(objs) if objs else None
        _sat_cache["t"] = now if objs else now - (_SAT_TTL - 60.0)  # retry empties after 60 s
        return _sat_cache["names"], _sat_cache["arr"]


def _observer_ecef_km(lat, lon, alt_m):
    phi, lam = math.radians(lat), math.radians(lon)
    n = _A_KM / math.sqrt(1.0 - _E2 * math.sin(phi) ** 2)
    h = alt_m / 1000.0
    return np.array([(n + h) * math.cos(phi) * math.cos(lam),
                     (n + h) * math.cos(phi) * math.sin(lam),
                     (n * (1.0 - _E2) + h) * math.sin(phi)])


def _teme_to_ecef(r_teme, theta_rad):
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.stack([r_teme[:, 0] * c + r_teme[:, 1] * s,
                     -r_teme[:, 0] * s + r_teme[:, 1] * c,
                     r_teme[:, 2]], axis=1)


def _ecef_to_altaz(r_ecef, lat, lon, alt_m):
    d = r_ecef - _observer_ecef_km(lat, lon, alt_m)
    phi, lam = math.radians(lat), math.radians(lon)
    east = -math.sin(lam) * d[:, 0] + math.cos(lam) * d[:, 1]
    north = (-math.sin(phi) * math.cos(lam) * d[:, 0] - math.sin(phi) * math.sin(lam) * d[:, 1]
             + math.cos(phi) * d[:, 2])
    up = (math.cos(phi) * math.cos(lam) * d[:, 0] + math.cos(phi) * math.sin(lam) * d[:, 1]
          + math.sin(phi) * d[:, 2])
    rng = np.sqrt(east ** 2 + north ** 2 + up ** 2)
    alt = np.rad2deg(np.arcsin(np.clip(up / rng, -1.0, 1.0)))
    az = np.rad2deg(np.arctan2(east, north)) % 360.0
    return alt, az


def _propagate_uncached(lat, lon, alt_m, when):
    names, arr = _sat_catalogue()
    if arr is None:
        return None
    from sgp4.api import jday
    w = _utc(when)
    jd, fr = jday(w.year, w.month, w.day, w.hour, w.minute, w.second + w.microsecond * 1e-6)
    e, r, _ = arr.sgp4(np.array([jd]), np.array([fr]))
    ok = e[:, 0] == 0
    with np.errstate(invalid="ignore"):
        ecef = _teme_to_ecef(r[:, 0, :], math.radians(_gmst_deg(jd + fr)))
        alt, az = _ecef_to_altaz(ecef, lat, lon, alt_m)
    return names, ok, alt, az, ecef


def get_visible_satellites(lat, lon, alt_m=0.0, when=None, limit=10) -> list:
    res = _propagate(lat, lon, alt_m, when)
    if res is None:
        return []
    names, ok, alt, az, _ = res
    idx = np.flatnonzero(ok & (alt > 0))
    idx = idx[np.argsort(-alt[idx])][:limit]
    return [{"name": names[i], "altitude_deg": round(float(alt[i]), 2),
             "azimuth_deg": round(float(az[i]), 2)} for i in idx]


def _subpoint(ecef):
    x, y, z = float(ecef[0]), float(ecef[1]), float(ecef[2])
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1.0 - _E2))
    for _ in range(4):
        n = _A_KM / math.sqrt(1.0 - _E2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1.0 - _E2 * n / (n + h)))
    return math.degrees(lat), math.degrees(math.atan2(y, x))


async def get_iss_position(observer_lat, observer_lon, when) -> dict:
    res = _propagate(observer_lat, observer_lon, 0.0, when)
    if res is not None:
        names, ok, alt, az, ecef = res
        for i, nm in enumerate(names):
            if nm.upper().startswith("ISS") and ok[i]:
                la, lo = _subpoint(ecef[i])
                return {"latitude": round(la, 3), "longitude": round(lo, 3),
                        "altitude_deg": round(float(alt[i]), 2), "azimuth_deg": round(float(az[i]), 2),
                        "visible": bool(alt[i] > 0), "available": True,
                        "timestamp": int(_utc(when).timestamp())}
    return {"visible": False, "available": False, "reason": "ISS not found in TLE catalogue"}


def warm() -> None:
    """Load the star catalogue and the current planet block in the background."""
    def run():
        try:
            for _ in range(6):
                if _load_catalogue() is not None:
                    break
                time.sleep(10)
            now = datetime.now(timezone.utc)
            cat = _load_catalogue()
            if cat is not None:
                _stars_of_date(cat, now)
            _compute_block(int(now.timestamp() // _BLOCK_S))
            get_planet_positions(0.0, 0.0, now, 0.0, 45.0, 0.0, 100, 100)
            _propagate(0.0, 0.0, 0.0, now)
        except Exception as exc:  # pragma: no cover
            logger.warning("scene_fast warm-up failed: %s", exc)
    threading.Thread(target=run, daemon=True).start()

_last_prop: dict = {}


def _propagate(lat, lon, alt_m, when):
    """One propagation per (instant, place): satellites and ISS share it within a frame."""
    key = (round(_utc(when).timestamp(), 1), lat, lon, alt_m)
    hit = _last_prop.get("v")
    if hit is not None and hit[0] == key:
        return hit[1]
    val = _propagate_uncached(lat, lon, alt_m, when)
    _last_prop["v"] = (key, val)
    return val