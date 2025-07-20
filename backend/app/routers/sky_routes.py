from fastapi import APIRouter, Query
from typing import Optional
from app.utils.sky_tools import get_visible_objects

router = APIRouter(prefix="/api/sky", tags=["Sky"])

@router.get("/focus")
def sky_focus(
    lat: float = Query(..., description="Latitude of the user"),
    lon: float = Query(..., description="Longitude of the user"),
    azimuth: float = Query(..., description="Azimuth angle in degrees"),
    radius: Optional[float] = Query(10, description="Angular radius (default 10 degrees)")
):
    data = get_visible_objects(lat, lon, azimuth, radius)
    return {"success": True, "data": data}