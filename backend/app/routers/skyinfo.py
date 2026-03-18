"""
app/routers/skyinfo.py

Sky Information Router
======================
Provides sky condition and celestial timing endpoints for the Eye in the Sky app.

Endpoints
---------
  GET /skyinfo/moon-phase      — Moon phase (local calc, no API key needed)
  GET /skyinfo/visibility      — Stargazing visibility score from OpenWeather
  GET /skyinfo/rise-set        — Star/planet rise & set times via AstronomyAPI
  GET /skyinfo/scene           — Full AR sky scene (master frame endpoint)
  GET /skyinfo/planets         — Planet positions for observer location
  GET /skyinfo/iss             — Live ISS position + visibility flag
  GET /skyinfo/events          — Upcoming celestial events
  GET /skyinfo/star/{name}     — Tap-to-learn star detail

Sources
-------
  Moon phase   → skyController.get_moon_phase_local()   (pure math, no API)
  Visibility   → skyController.get_sky_visibility()     (OpenWeather)
  Rise/Set     → app.utils.astronomy.get_star_rise_set() (AstronomyAPI)
  Everything else → skyController (astropy + sgp4 + httpx)
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.controllers.skyController import (
    get_celestial_events,
    get_closest_constellation,
    get_full_sky_scene,
    get_iss_position,
    get_moon_phase_local,
    get_planet_positions,
    get_sky_visibility,
    get_star_detail,
    get_visible_stars,
)
from app.utils.astronomy import get_star_rise_set

router = APIRouter(prefix="/skyinfo", tags=["Sky Information"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_datetime(date_str: Optional[str]) -> datetime:
    """
    Parse an ISO 8601 datetime string or YYYY-MM-DD date string to a UTC
    datetime. Falls back to now() if no value is provided.
    """
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid datetime format '{date_str}'. Use YYYY-MM-DD or ISO 8601.",
        )


# ═════════════════════════════════════════════════════════════════════════════
#  Moon phase
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/moon-phase",
    summary="Moon phase",
    response_description="Phase name, illumination %, and age in days",
)
async def moon_phase(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
    date: Optional[str] = Query(
        None,
        description="UTC date/time in YYYY-MM-DD or ISO 8601 format. Defaults to now.",
    ),
):
    """
    Returns the current moon phase using a local synodic-cycle calculation —
    no external API key required.

    Includes phase name (e.g. 'Waxing Gibbous'), illumination percentage,
    and age in days since last new moon.
    """
    when = _parse_datetime(date)
    return {
        "observer":   {"lat": lat, "lon": lon},
        "datetime":   when.isoformat(),
        "moon_phase": get_moon_phase_local(when),
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Visibility / weather
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/visibility",
    summary="Stargazing visibility forecast",
    response_description="Score 0–100, cloud cover, humidity, dew point warning",
)
async def visibility_forecast(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
):
    """
    Computes a stargazing visibility score (0–100) from live OpenWeather data.

    Score = 100 − cloud_cover%. A humidity penalty of −10 is applied when
    humidity exceeds 85%. Also returns a dew point warning when the dew point
    is within 2°C of air temperature (lens fogging risk).
    """
    data = await get_sky_visibility(lat, lon)
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=data["error"],
        )
    return {"observer": {"lat": lat, "lon": lon}, "visibility": data}


# ═════════════════════════════════════════════════════════════════════════════
#  Rise / set times
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/rise-set",
    summary="Star and planet rise/set times",
    response_description="Rise, transit, and set times for stars and planets",
)
async def star_rise_set(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Returns rise, transit, and set times for stars and planets at the given
    location and date. Powered by AstronomyAPI — requires ASTRONOMY_API_KEY.
    """
    data = await get_star_rise_set(lat, lon, date)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=data["error"],
        )
    return {"observer": {"lat": lat, "lon": lon}, "date": date, "star_rise_set": data}


# ═════════════════════════════════════════════════════════════════════════════
#  Full AR sky scene (master frame endpoint)
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/scene",
    summary="Full AR sky scene",
    response_description="Stars, planets, constellation, moon, ISS, satellites",
)
async def full_sky_scene(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
    az: float = Query(..., description="Device azimuth — compass bearing (0–360, N=0)"),
    alt: float = Query(..., description="Device tilt above horizon (degrees, −90 to 90)"),
    roll: float = Query(0.0, description="Device roll around pointing axis (degrees)"),
    screen_w: int = Query(1080, description="AR canvas width in pixels"),
    screen_h: int = Query(1920, description="AR canvas height in pixels"),
    fov_h: float = Query(60.0, description="Camera horizontal field of view (degrees)"),
    fov_v: float = Query(110.0, description="Camera vertical field of view (degrees)"),
    mag_limit: float = Query(5.5, description="Faintest magnitude to include (lower = brighter only)"),
    when: Optional[str] = Query(None, description="UTC datetime ISO 8601. Defaults to now."),
    planets: bool = Query(True, description="Include planet positions"),
    satellites: bool = Query(True, description="Include visible satellites"),
    iss: bool = Query(True, description="Include ISS position"),
    events: bool = Query(False, description="Include upcoming celestial events (slower)"),
    weather: bool = Query(False, description="Include visibility score (requires API key)"),
):
    """
    Master AR frame endpoint — called by the Kotlin app once per gyroscope
    update cycle. Returns the complete sky scene: all visible stars with screen
    (x, y) coordinates, planet positions, the closest constellation, moon phase,
    ISS visibility, and optionally satellites, events, and weather.

    Toggle `events` and `weather` off for high-frequency frame calls to keep
    response times under 100 ms.
    """
    when_dt = _parse_datetime(when)
    scene = await get_full_sky_scene(
        lat=lat,
        lon=lon,
        device_az=az,
        device_alt=alt,
        device_roll=roll,
        screen_w=screen_w,
        screen_h=screen_h,
        fov_h=fov_h,
        fov_v=fov_v,
        mag_limit=mag_limit,
        when=when_dt,
        include_planets=planets,
        include_satellites=satellites,
        include_iss=iss,
        include_events=events,
        include_weather=weather,
    )
    return scene


# ═════════════════════════════════════════════════════════════════════════════
#  Planet positions
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/planets",
    summary="Solar system body positions",
    response_description="Alt/Az and screen coords for all visible planets",
)
async def planet_positions(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
    az: float = Query(..., description="Device azimuth (degrees, N=0)"),
    alt: float = Query(..., description="Device tilt above horizon (degrees)"),
    roll: float = Query(0.0, description="Device roll (degrees)"),
    screen_w: int = Query(1080, description="Screen width in pixels"),
    screen_h: int = Query(1920, description="Screen height in pixels"),
    fov_h: float = Query(60.0, description="Horizontal FOV (degrees)"),
    fov_v: float = Query(110.0, description="Vertical FOV (degrees)"),
    when: Optional[str] = Query(None, description="UTC datetime ISO 8601. Defaults to now."),
):
    """
    Returns Alt/Az and screen pixel positions for all solar system bodies
    currently above the horizon. Uses astropy's built-in ephemeris —
    no external API key required.
    """
    when_dt = _parse_datetime(when)
    planets = get_planet_positions(
        lat, lon, when_dt,
        az, alt, roll,
        screen_w, screen_h, fov_h, fov_v,
    )
    return {
        "observer": {"lat": lat, "lon": lon},
        "datetime": when_dt.isoformat(),
        "planets":  planets,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  ISS live position
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/iss",
    summary="ISS live position",
    response_description="ISS lat/lon, Alt/Az from observer, and visibility flag",
)
async def iss_position(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
):
    """
    Returns the ISS's current geographic position (lat/lon) and computes
    whether it is above the observer's horizon at this moment.

    Data sourced from Open Notify — no API key required.
    """
    when = datetime.now(timezone.utc)
    data = await get_iss_position(lat, lon, when)
    if "error" in data and not data.get("visible"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=data["error"],
        )
    return {"observer": {"lat": lat, "lon": lon}, "iss": data}


# ═════════════════════════════════════════════════════════════════════════════
#  Celestial events
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/events",
    summary="Upcoming celestial events",
    response_description="Meteor showers, eclipses, conjunctions from AstronomyAPI",
)
async def celestial_events(
    lat: float = Query(..., description="Observer latitude (decimal degrees)"),
    lon: float = Query(..., description="Observer longitude (decimal degrees)"),
):
    """
    Returns upcoming celestial events for the observer's location.
    Powered by AstronomyAPI — requires ASTRONOMY_API_KEY in your .env.
    """
    data = await get_celestial_events(lat, lon)
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=data["error"],
        )
    return {"observer": {"lat": lat, "lon": lon}, "events": data}


# ═════════════════════════════════════════════════════════════════════════════
#  Star detail (tap-to-learn)
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/star/{star_name}",
    summary="Star detail — tap to learn",
    response_description="Full star data enriched with constellation mythology",
)
async def star_detail(star_name: str):
    """
    Returns full catalogue data for a named star plus the mythology,
    discoverer, and brightest-star info for its parent constellation.

    Used by the Kotlin AR overlay when the user taps a star label.
    Matches on common name, Bayer designation, or HR identifier.
    """
    detail = get_star_detail(star_name)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star '{star_name}' not found in catalogue.",
        )
    return {"star": detail}