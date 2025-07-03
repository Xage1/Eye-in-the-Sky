from fastapi import APIRouter, Query
from app.utils.weather import get_visibility_forecast
from app.utils.astronomy import get_events

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("/night-sky")
async def night_sky_events(lat: float, lon: float):
    astronomy = await get_events(lat, lon)
    weather = await get_visibility_forecast(lat, lon)
    return {"astronomy": astronomy, "weather": weather}