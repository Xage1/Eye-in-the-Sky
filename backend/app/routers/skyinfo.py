from fastapi import APIRouter, Query
from app.utils.astronomy import (
    get_moon_phase,
    get_visibility_forecast,
    get_star_rise_set,
)

router = APIRouter(prefix="/skyinfo", tags=["Sky Information"])

@router.get("/moon-phase")
async def moon_phase(
    lat: float = Query(..., description="Latitude of the observer's location"),
    lon: float = Query(..., description="Longitude of the observer's location"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Get the moon phase for a given latitude, longitude, and date."""
    data = await get_moon_phase(lat, lon, date)
    return {"moon_phase": data}

@router.get("/visibility")
async def visibility_forecast(
    lat: float = Query(..., description="Latitude of the observer's location"),
    lon: float = Query(..., description="Longitude of the observer's location")
):
    """Get visibility forecast for a given latitude and longitude."""
    data = await get_visibility_forecast(lat, lon)
    return {"visibility": data}

@router.get("/rise-set")
async def star_rise_set(
    lat: float = Query(..., description="Latitude of the observer's location"),
    lon: float = Query(..., description="Longitude of the observer's location"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Get star rise and set times for a given latitude, longitude, and date."""
    data = await get_star_rise_set(lat, lon, date)
    return {"star_rise_set": data}