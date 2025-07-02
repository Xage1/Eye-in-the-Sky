from fastapi import APIRouter, Query
from app.utils.astronomy import get_events

router = APIRouter(prefix="/events", tags=["Celestial Events"])

@router.get("/")
async def events(lat: float = Query(...), lon: float = Query(...)):
    return await get_events(lat, lon)