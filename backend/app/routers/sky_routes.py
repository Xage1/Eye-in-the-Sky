from fastapi import APIRouter, Query
from app.utils.sky_tools import identify_visible_constellations, find_nearby_stars
from app.services.astronomy_service import get_astronomy_data

router = APIRouter(prefix="/sky", tags=["Sky"])

@router.get("/focus")
def sky_focus(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    azimuth: float = Query(0.0, ge=0, le=360, description="Viewing direction in degrees (0=N, 90=E). Defaults to North."),
    altitude: float = Query(45.0, ge=0, le=90, description="Viewing elevation above the horizon in degrees."),
    radius: float = Query(15.0, gt=0, le=90, description="Search radius in degrees for nearby stars."),
):
    """
    Given the user's location and viewing direction, return the constellation in view,
    the brightest nearby stars, and astronomy info.
    """
    constellation = identify_visible_constellations(lat, lon, azimuth, altitude)
    stars = find_nearby_stars(lat, lon, azimuth, altitude, radius)
    astronomy_info = get_astronomy_data(lat, lon)

    return {
        "location": {"latitude": lat, "longitude": lon},
        "view": {"azimuth": azimuth, "altitude": altitude, "radius": radius},
        "constellation": constellation,
        "stars": stars,
        "astronomy": astronomy_info,
    }