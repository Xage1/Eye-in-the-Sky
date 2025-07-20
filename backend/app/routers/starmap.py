from fastapi import APIRouter, Query
from app.utils.astronomy import get_constellation_data

router = APIRouter(prefix="/starmap", tags=["Star Map"])

@router.get("/")
async def starmap(lat: float = Query(..., description="Latitude of the observer's location"),
                  lon: float = Query(..., description="Longitude of the observer's location"),
                  date: str = Query(None, description="Date in YYYY-MM-DD format (optional)")):
    """
    Get star map data for a given latitude, longitude, and optional date.
    """
    try:
        data = await get_constellation_data(lat, lon, date)
        return {"constellations": data}
    except Exception as e:
        return {"error": str(e)}