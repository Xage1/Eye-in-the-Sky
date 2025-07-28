from fastapi import APIRouter, Query
from typing import Optional
from app.utils.sky_tools import identify_visible_constellations, find_nearby_stars
from app.services.astronomy_service import get_astronomy_data

router = APIRouter(prefix="/sky", tags=["Sky"])

@router.get("/focus")
def sky_focus(lat: float = Query(...), lon: float = Query(...), azimuth: Optional[float] = None, altitude: Optional[float] = None):
    """
    Given user's location and optional viewing direction, return visible constellations, nearby stars, and astronomy info.
    """
    # Constellation & star lookup
    visible_constellations = identify_visible_constellations(lat, lon, azimuth)
    nearby_stars = find_nearby_stars(lat, lon, azimuth, altitude)

    # Astronomy API call
    astronomy_info = get_astronomy_data(lat, lon)

    return {
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "constellations": visible_constellations,
        "stars": nearby_stars,
        "astronomy": astronomy_info
    }