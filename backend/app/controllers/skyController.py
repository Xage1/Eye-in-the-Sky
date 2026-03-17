"""
app/controllers/skyController.py

Eye in the Sky — Sky Controller
================================
The central brain of the AR star map. Every frame the Kotlin frontend
sends the user's GPS position, device orientation angles, and a UTC
timestamp; this controller returns a fully-resolved sky scene:

  • All stars above the horizon, with pixel (x, y) for the AR canvas
  • The closest constellation to the user's pointing direction
  • Live planet positions (Alt/Az + screen coords)
  • Upcoming celestial events for the location
  • Moon phase
  • ISS position and whether it is currently visible overhead

Pipeline (per request)
-----------------------
  GPS + UTC  →  Local Sidereal Time (LST)
  LST + RA   →  Hour Angle (HA)
  HA + Dec + Lat  →  Altitude / Azimuth   (spherical trig)
  Device rotation matrix + Alt/Az  →  camera-relative unit vector
  Unit vector + FOV + screen dims  →  pixel (x, y)

External dependencies used
---------------------------
  astropy   — SkyCoord, AltAz, EarthLocation, Time
  sgp4      — satellite TLE propagation (via satellite_service)
  httpx     — async calls to AstronomyAPI, OpenWeather, Open Notify
  json      — local constellation / star catalogue
"""

from __future__ import annotations

import json
import math
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
    get_body,
    solar_system_ephemeris,
)
from astropy.time import Time
import astropy.units as u

from app.services.satellite_service import get_visible_satellites

logger = logging.getLogger(__name__)

# ── Data paths ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_STARS_PATH = _DATA_DIR / "stars.json"
_CONSTELLATIONS_PATH = _DATA_DIR / "constellations.json"

# ── External API config ───────────────────────────────────────────────────────
_ASTRONOMY_API_KEY = os.getenv("ASTRONOMY_API_KEY", "")
_WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
_ASTRONOMY_BASE = "https://api.astronomyapi.com/api/v2"
_OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5"
_ISS_URL = "http://api.open-notify.org/iss-now.json"

# ── Planets tracked by astropy solar_system_ephemeris ────────────────────────
_PLANETS = [
    "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "moon", "sun",
]

# ── Magnitude limit — only stars brighter than this shown by default ──────────
_DEFAULT_MAG_LIMIT: float = 5.5


# ═════════════════════════════════════════════════════════════════════════════
#  Data loaders — cached at module level, loaded once on first call
# ═════════════════════════════════════════════════════════════════════════════

_stars_cache: list[dict] | None = None
_constellations_cache: dict | None = None


def _load_stars() -> list[dict]:
    """Load the stars catalogue from stars.json. Cached after first call."""
    global _stars_cache
    if _stars_cache is None:
        if not _STARS_PATH.exists():
            logger.warning("stars.json not found at %s — returning empty catalogue", _STARS_PATH)
            _stars_cache = []
        else:
            with _STARS_PATH.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            # Support both {"stars": [...]} and bare list formats
            _stars_cache = raw.get("stars", raw) if isinstance(raw, dict) else raw
    return _stars_cache


def _load_constellations() -> dict:
    """Load constellation data from constellations.json. Cached after first call."""
    global _constellations_cache
    if _constellations_cache is None:
        if not _CONSTELLATIONS_PATH.exists():
            logger.warning("constellations.json not found — returning empty dict")
            _constellations_cache = {}
        else:
            with _CONSTELLATIONS_PATH.open("r", encoding="utf-8") as f:
                _constellations_cache = json.load(f)
    return _constellations_cache


# ═════════════════════════════════════════════════════════════════════════════
#  Core maths — coordinate transforms
# ═════════════════════════════════════════════════════════════════════════════

def _build_altaz_frame(lat: float, lon: float, when: datetime) -> AltAz:
    """
    Build an astropy AltAz frame for a specific observer location and time.

    Parameters
    ----------
    lat   : observer latitude in decimal degrees
    lon   : observer longitude in decimal degrees
    when  : UTC datetime (timezone-aware or naive — treated as UTC)
    """
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    t = Time(when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when)
    return AltAz(obstime=t, location=location)


def _radec_to_altaz(
    ra_deg: float,
    dec_deg: float,
    frame: AltAz,
) -> tuple[float, float]:
    """
    Convert RA/Dec (ICRS, degrees) to Altitude/Azimuth (degrees).

    Returns
    -------
    (altitude_deg, azimuth_deg)
      altitude : degrees above horizon, negative = below
      azimuth  : degrees clockwise from North (0–360)
    """
    coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
    altaz = coord.transform_to(frame)
    return float(altaz.alt.deg), float(altaz.az.deg)


def _altaz_to_screen(
    alt_deg: float,
    az_deg: float,
    device_az_deg: float,
    device_alt_deg: float,
    device_roll_deg: float,
    fov_h_deg: float,
    fov_v_deg: float,
    screen_w: int,
    screen_h: int,
) -> tuple[float | None, float | None]:
    """
    Project a sky point (Alt/Az) onto the device screen.

    The device is pointing in direction (device_az, device_alt) and rotated
    by device_roll around the pointing axis.  We compute the angular offset
    between the sky point and the device's pointing direction, apply the roll
    rotation, then scale to screen pixels using the camera FOV.

    Returns
    -------
    (x, y) in screen pixels, or (None, None) if the point is behind the device.
    """
    # ── Convert both to unit vectors in a local ENU frame ──────────────────
    def _to_unit(az_r: float, alt_r: float) -> np.ndarray:
        """Alt/Az → unit vector. Az=0 is North, increases clockwise."""
        cos_alt = math.cos(alt_r)
        return np.array([
            cos_alt * math.sin(az_r),   # East
            cos_alt * math.cos(az_r),   # North
            math.sin(alt_r),            # Up
        ])

    az_r   = math.radians(az_deg)
    alt_r  = math.radians(alt_deg)
    d_az_r = math.radians(device_az_deg)
    d_al_r = math.radians(device_alt_deg)
    roll_r = math.radians(device_roll_deg)

    target  = _to_unit(az_r, alt_r)
    forward = _to_unit(d_az_r, d_al_r)

    # ── Dot product gives cosine of angle between vectors ──────────────────
    dot = float(np.clip(np.dot(target, forward), -1.0, 1.0))

    # Point is behind the device — don't render
    if dot < 0:
        return None, None

    # ── Build camera coordinate frame: forward / right / up ────────────────
    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    r_norm = np.linalg.norm(right)
    if r_norm < 1e-6:
        # Device pointing straight up or down — degenerate, use East as right
        right = np.array([1.0, 0.0, 0.0])
    else:
        right = right / r_norm

    cam_up = np.cross(right, forward)

    # ── Apply device roll around the forward axis ───────────────────────────
    cos_r, sin_r = math.cos(roll_r), math.sin(roll_r)
    right_rolled  =  cos_r * right  + sin_r * cam_up
    up_rolled     = -sin_r * right  + cos_r * cam_up

    # ── Project target onto rolled camera plane ─────────────────────────────
    offset = target - dot * forward
    o_norm = np.linalg.norm(offset)

    if o_norm < 1e-9:
        # Star is exactly at screen centre
        return float(screen_w / 2), float(screen_h / 2)

    offset_unit = offset / o_norm
    angle_from_centre = math.acos(dot)   # radians

    # Angular offsets in camera right / up directions
    ang_x = angle_from_centre * float(np.dot(offset_unit, right_rolled))
    ang_y = angle_from_centre * float(np.dot(offset_unit, up_rolled))

    # ── Scale to pixels using FOV ───────────────────────────────────────────
    half_w = screen_w / 2.0
    half_h = screen_h / 2.0

    px = half_w + (ang_x / math.radians(fov_h_deg / 2.0)) * half_w
    py = half_h - (ang_y / math.radians(fov_v_deg / 2.0)) * half_h

    # Clip to screen bounds — return None if entirely off-screen
    margin = 50  # px — allow slight off-screen for labels at edges
    if not (-margin <= px <= screen_w + margin and -margin <= py <= screen_h + margin):
        return None, None

    return round(px, 1), round(py, 1)


# ═════════════════════════════════════════════════════════════════════════════
#  Stars
# ═════════════════════════════════════════════════════════════════════════════

def get_visible_stars(
    lat: float,
    lon: float,
    when: datetime,
    device_az: float,
    device_alt: float,
    device_roll: float,
    screen_w: int,
    screen_h: int,
    fov_h: float = 60.0,
    fov_v: float = 110.0,
    mag_limit: float = _DEFAULT_MAG_LIMIT,
) -> list[dict]:
    """
    Return all stars above the horizon that fall within the device's FOV.

    Each entry includes:
      name, constellation, magnitude, ra, dec,
      altitude_deg, azimuth_deg, screen_x, screen_y,
      distance_from_centre_deg
    """
    frame = _build_altaz_frame(lat, lon, when)
    stars = _load_stars()
    results: list[dict] = []

    for star in stars:
        try:
            mag = star.get("mag") or star.get("magnitude")
            if mag is None or float(mag) > mag_limit:
                continue

            ra  = float(star.get("ra")  or star.get("ra_deg")  or 0)
            dec = float(star.get("dec") or star.get("dec_deg") or 0)

            alt, az = _radec_to_altaz(ra, dec, frame)
            if alt < 0:
                continue

            sx, sy = _altaz_to_screen(
                alt, az,
                device_az, device_alt, device_roll,
                fov_h, fov_v, screen_w, screen_h,
            )
            if sx is None:
                continue

            # Angular distance from screen centre (for tap-to-select matching)
            d_az  = az  - device_az
            d_alt = alt - device_alt
            dist_deg = math.sqrt(d_az ** 2 + d_alt ** 2)

            results.append({
                "name":           star.get("name") or star.get("proper_name") or "Unknown",
                "constellation":  star.get("constellation", ""),
                "magnitude":      round(float(mag), 2),
                "ra":             round(ra, 4),
                "dec":            round(dec, 4),
                "altitude_deg":   round(alt, 2),
                "azimuth_deg":    round(az, 2),
                "screen_x":       sx,
                "screen_y":       sy,
                "distance_from_centre_deg": round(dist_deg, 2),
            })

        except Exception as exc:
            logger.debug("Skipping star due to error: %s", exc)
            continue

    # Sort by magnitude (brightest first) so the AR canvas draws dim stars last
    return sorted(results, key=lambda s: s["magnitude"])


# ═════════════════════════════════════════════════════════════════════════════
#  Constellations
# ═════════════════════════════════════════════════════════════════════════════

def get_closest_constellation(
    lat: float,
    lon: float,
    when: datetime,
    device_az: float,
    device_alt: float = 45.0,
) -> dict | None:
    """
    Find the constellation whose centroid is closest to the device's pointing
    direction and is above the horizon.

    Uses the mean RA/Dec of the constellation's major stars as its centroid.
    Returns full constellation metadata from constellations.json, enriched
    with Alt/Az and angular distance from the device's pointing direction.
    """
    frame    = _build_altaz_frame(lat, lon, when)
    stars    = _load_stars()
    consts   = _load_constellations()

    # Build a quick name → star lookup from the catalogue
    star_lookup: dict[str, dict] = {}
    for s in stars:
        name = (s.get("name") or s.get("proper_name") or "").lower()
        if name:
            star_lookup[name] = s

    # Device pointing direction as an Alt/Az SkyCoord
    device_coord = SkyCoord(
        az=device_az * u.deg,
        alt=device_alt * u.deg,
        frame=frame,
    )

    closest: dict | None = None
    min_sep = float("inf")

    for const_name, const_data in consts.items():
        try:
            major_stars = const_data.get("major_stars", [])
            if not major_stars:
                continue

            ras, decs = [], []
            for star_name in major_stars:
                match = star_lookup.get(star_name.lower())
                if match:
                    ras.append(float(match.get("ra") or match.get("ra_deg") or 0))
                    decs.append(float(match.get("dec") or match.get("dec_deg") or 0))

            if not ras:
                continue

            centroid_ra  = sum(ras)  / len(ras)
            centroid_dec = sum(decs) / len(decs)

            cent_coord = SkyCoord(
                ra=centroid_ra * u.deg,
                dec=centroid_dec * u.deg,
                frame="icrs",
            )
            cent_altaz = cent_coord.transform_to(frame)

            # Skip below-horizon constellations
            if cent_altaz.alt.deg < 0:
                continue

            sep = device_coord.separation(cent_altaz).deg

            if sep < min_sep:
                min_sep = sep
                closest = {
                    **const_data,
                    "name":            const_name,
                    "altitude_deg":    round(float(cent_altaz.alt.deg), 2),
                    "azimuth_deg":     round(float(cent_altaz.az.deg), 2),
                    "separation_deg":  round(sep, 2),
                    "centroid_ra":     round(centroid_ra, 4),
                    "centroid_dec":    round(centroid_dec, 4),
                }
        except Exception as exc:
            logger.debug("Error processing constellation %s: %s", const_name, exc)
            continue

    return closest


# ═════════════════════════════════════════════════════════════════════════════
#  Planets
# ═════════════════════════════════════════════════════════════════════════════

def get_planet_positions(
    lat: float,
    lon: float,
    when: datetime,
    device_az: float,
    device_alt: float,
    device_roll: float,
    screen_w: int,
    screen_h: int,
    fov_h: float = 60.0,
    fov_v: float = 110.0,
) -> list[dict]:
    """
    Compute Alt/Az and screen positions for all solar system bodies.

    Uses astropy's built-in solar system ephemeris (no external API call).
    Returns only bodies that are above the horizon; screen_x/screen_y are
    None for bodies outside the current FOV.
    """
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    t = Time(when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when)
    frame = AltAz(obstime=t, location=location)
    results: list[dict] = []

    with solar_system_ephemeris.set("builtin"):
        for body_name in _PLANETS:
            try:
                body = get_body(body_name, t, location)
                body_altaz = body.transform_to(frame)
                alt = float(body_altaz.alt.deg)
                az  = float(body_altaz.az.deg)

                if alt < 0:
                    continue

                sx, sy = _altaz_to_screen(
                    alt, az,
                    device_az, device_alt, device_roll,
                    fov_h, fov_v, screen_w, screen_h,
                )

                results.append({
                    "name":         body_name.capitalize(),
                    "altitude_deg": round(alt, 2),
                    "azimuth_deg":  round(az, 2),
                    "screen_x":     sx,
                    "screen_y":     sy,
                    "ra_deg":       round(float(body.ra.deg), 4),
                    "dec_deg":      round(float(body.dec.deg), 4),
                })
            except Exception as exc:
                logger.debug("Planet %s error: %s", body_name, exc)
                continue

    return results


# ═════════════════════════════════════════════════════════════════════════════
#  Moon phase
# ═════════════════════════════════════════════════════════════════════════════

def get_moon_phase_local(when: datetime) -> dict:
    """
    Compute moon phase from the synodic cycle without an external API call.

    Returns phase name, illumination percentage (0–100), and age in days.
    Known new moon anchor: 2000-01-06 18:14 UTC (J2000 epoch reference).
    """
    SYNODIC_MONTH = 29.53058867  # days
    ANCHOR = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

    now = when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when
    delta_days = (now - ANCHOR).total_seconds() / 86400.0
    age = delta_days % SYNODIC_MONTH  # days since last new moon

    # Illumination: 0 at new moon, 1 at full moon
    illumination = (1 - math.cos(2 * math.pi * age / SYNODIC_MONTH)) / 2

    if age < 1.85:
        phase = "New Moon"
    elif age < 7.38:
        phase = "Waxing Crescent"
    elif age < 9.22:
        phase = "First Quarter"
    elif age < 14.77:
        phase = "Waxing Gibbous"
    elif age < 16.61:
        phase = "Full Moon"
    elif age < 22.15:
        phase = "Waning Gibbous"
    elif age < 23.99:
        phase = "Last Quarter"
    elif age < 29.53:
        phase = "Waning Crescent"
    else:
        phase = "New Moon"

    return {
        "phase_name":          phase,
        "age_days":            round(age, 2),
        "illumination_pct":    round(illumination * 100, 1),
        "synodic_month_days":  round(SYNODIC_MONTH, 5),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  ISS position
# ═════════════════════════════════════════════════════════════════════════════

async def get_iss_position(
    observer_lat: float,
    observer_lon: float,
    when: datetime,
) -> dict:
    """
    Fetch ISS live position from Open Notify and compute whether it is
    currently visible from the observer's location (above horizon).

    Falls back to a cached/empty result if the API is unreachable.
    """
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(_ISS_URL)
            resp.raise_for_status()
            data = resp.json()

        iss_lat = float(data["iss_position"]["latitude"])
        iss_lon = float(data["iss_position"]["longitude"])

        # Compute ISS Alt/Az from observer using astropy
        frame   = _build_altaz_frame(observer_lat, observer_lon, when)
        iss_loc = EarthLocation(
            lat=iss_lat * u.deg,
            lon=iss_lon * u.deg,
            height=408_000 * u.m,  # typical ISS orbital altitude ~408 km
        )
        iss_gcrs   = iss_loc.get_gcrs(Time(when))
        iss_altaz  = iss_gcrs.transform_to(frame)

        alt = float(iss_altaz.alt.deg)
        az  = float(iss_altaz.az.deg)

        return {
            "latitude":     iss_lat,
            "longitude":    iss_lon,
            "altitude_deg": round(alt, 2),
            "azimuth_deg":  round(az, 2),
            "visible":      alt > 0,
            "timestamp":    data.get("timestamp"),
        }

    except Exception as exc:
        logger.warning("ISS position fetch failed: %s", exc)
        return {"error": str(exc), "visible": False}


# ═════════════════════════════════════════════════════════════════════════════
#  Celestial events
# ═════════════════════════════════════════════════════════════════════════════

async def get_celestial_events(lat: float, lon: float) -> dict:
    """
    Fetch upcoming celestial events from AstronomyAPI for the observer's
    location. Returns raw API payload or a graceful error dict.
    """
    if not _ASTRONOMY_API_KEY:
        return {"error": "ASTRONOMY_API_KEY not configured"}

    url = f"{_ASTRONOMY_BASE}/events"
    headers = {"Authorization": f"Bearer {_ASTRONOMY_API_KEY}"}
    params  = {"latitude": lat, "longitude": lon}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return {"error": f"AstronomyAPI {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"error": str(exc)}


# ═════════════════════════════════════════════════════════════════════════════
#  Sky visibility (weather)
# ═════════════════════════════════════════════════════════════════════════════

async def get_sky_visibility(lat: float, lon: float) -> dict:
    """
    Compute a stargazing visibility score (0–100) from OpenWeather data.

    Score = 100 − cloud_cover_pct.
    Additional context: humidity, wind speed, dew point warning.
    """
    if not _WEATHER_API_KEY:
        return {"error": "WEATHER_API_KEY not configured"}

    url = f"{_OPENWEATHER_BASE}/weather"
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": _WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        clouds     = data.get("clouds", {}).get("all", 0)
        humidity   = data.get("main", {}).get("humidity", 0)
        temp_c     = data.get("main", {}).get("temp", 0)
        dew_point  = temp_c - ((100 - humidity) / 5)   # Magnus approximation
        wind_ms    = data.get("wind", {}).get("speed", 0)
        visibility_m = data.get("visibility", 10000)

        score = max(0, 100 - clouds)

        # Humidity penalty: heavy moisture blurs seeing
        if humidity > 85:
            score = max(0, score - 10)

        return {
            "visibility_score":       score,
            "cloud_cover_pct":        clouds,
            "humidity_pct":           humidity,
            "temperature_c":          round(temp_c, 1),
            "dew_point_c":            round(dew_point, 1),
            "dew_point_warning":      dew_point >= temp_c - 2,
            "wind_speed_ms":          wind_ms,
            "visibility_m":           visibility_m,
            "sky_clear":              clouds < 25,
            "conditions":             data.get("weather", [{}])[0].get("description", ""),
        }
    except httpx.HTTPStatusError as exc:
        return {"error": f"OpenWeather {exc.response.status_code}"}
    except Exception as exc:
        return {"error": str(exc)}


# ═════════════════════════════════════════════════════════════════════════════
#  Star detail (tap-to-learn)
# ═════════════════════════════════════════════════════════════════════════════

def get_star_detail(star_name: str) -> dict | None:
    """
    Return full catalogue detail for a named star (tap-to-learn feature).
    Searches by common name, Bayer designation, or HR id (case-insensitive).
    Also enriches with constellation mythology from constellations.json.
    """
    stars  = _load_stars()
    consts = _load_constellations()
    query  = star_name.strip().lower()

    for star in stars:
        names = [
            str(star.get("name") or ""),
            str(star.get("proper_name") or ""),
            str(star.get("bayer") or ""),
            f"hr {star.get('id', '')}",
        ]
        if any(n.lower() == query for n in names if n):
            const_name = star.get("constellation", "")
            const_data = consts.get(const_name, {})
            return {
                **star,
                "constellation_detail": {
                    "name":          const_name,
                    "description":   const_data.get("description"),
                    "myth":          const_data.get("myth"),
                    "discoverer":    const_data.get("discoverer"),
                    "year":          const_data.get("year"),
                    "brightest_star": const_data.get("brightest_star"),
                },
            }
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  Full sky scene — master function called by the AR router each frame
# ═════════════════════════════════════════════════════════════════════════════

async def get_full_sky_scene(
    lat: float,
    lon: float,
    device_az: float,
    device_alt: float,
    device_roll: float = 0.0,
    screen_w: int = 1080,
    screen_h: int = 1920,
    fov_h: float = 60.0,
    fov_v: float = 110.0,
    mag_limit: float = _DEFAULT_MAG_LIMIT,
    when: Optional[datetime] = None,
    include_planets: bool = True,
    include_satellites: bool = True,
    include_iss: bool = True,
    include_events: bool = False,
    include_weather: bool = False,
) -> dict:
    """
    Master sky scene builder — called once per AR frame from the Kotlin app.

    Parameters
    ----------
    lat, lon          : observer GPS coordinates (decimal degrees)
    device_az         : compass azimuth the device is pointing (0–360, N=0)
    device_alt        : tilt of device above horizon in degrees (-90 to 90)
    device_roll       : roll rotation of device around its pointing axis
    screen_w, screen_h: AR canvas resolution in pixels
    fov_h, fov_v      : camera horizontal and vertical field of view in degrees
    mag_limit         : faintest star magnitude to include (lower = brighter)
    when              : UTC datetime for the scene (defaults to now)
    include_*         : toggle expensive sections off for high-frequency frames

    Returns
    -------
    Full scene dict with keys:
      timestamp, observer, pointing, stars, planets, constellation,
      moon_phase, satellites, iss, events, visibility
    """
    when = when or datetime.now(timezone.utc)

    scene: dict = {
        "timestamp": when.isoformat(),
        "observer":  {"lat": lat, "lon": lon},
        "pointing":  {
            "azimuth_deg":  device_az,
            "altitude_deg": device_alt,
            "roll_deg":     device_roll,
        },
    }

    # ── Stars ───────────────────────────────────────────────────────────────
    scene["stars"] = get_visible_stars(
        lat, lon, when,
        device_az, device_alt, device_roll,
        screen_w, screen_h, fov_h, fov_v,
        mag_limit=mag_limit,
    )

    # ── Closest constellation ───────────────────────────────────────────────
    scene["constellation"] = get_closest_constellation(
        lat, lon, when, device_az, device_alt
    )

    # ── Planets ─────────────────────────────────────────────────────────────
    if include_planets:
        scene["planets"] = get_planet_positions(
            lat, lon, when,
            device_az, device_alt, device_roll,
            screen_w, screen_h, fov_h, fov_v,
        )
    else:
        scene["planets"] = []

    # ── Moon phase (always included — no API call) ───────────────────────────
    scene["moon_phase"] = get_moon_phase_local(when)

    # ── ISS ─────────────────────────────────────────────────────────────────
    if include_iss:
        scene["iss"] = await get_iss_position(lat, lon, when)
    else:
        scene["iss"] = None

    # ── Visible satellites ───────────────────────────────────────────────────
    if include_satellites:
        try:
            scene["satellites"] = get_visible_satellites(
                lat, lon, alt_m=0.0, when=when, limit=15
            )
        except Exception as exc:
            logger.warning("Satellite fetch failed: %s", exc)
            scene["satellites"] = []
    else:
        scene["satellites"] = []

    # ── Celestial events (expensive — only on explicit request) ─────────────
    if include_events:
        scene["events"] = await get_celestial_events(lat, lon)
    else:
        scene["events"] = None

    # ── Weather / visibility score ───────────────────────────────────────────
    if include_weather:
        scene["visibility"] = await get_sky_visibility(lat, lon)
    else:
        scene["visibility"] = None

    return scene