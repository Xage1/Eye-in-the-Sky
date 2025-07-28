from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from app.utils.satellite_tools import get_visible_satellites

router = APIRouter()

@router.get("sky/satellites/visible")
def get_visible(lat: float = Query(...), lon: float = Query(...), alt: float = 0, when: Optional[str] = None):
    """
    Get a list of visible satellites from the observer's location at a given UTC time.
    """

    try: 
        dt = datetime.fromisoformat(when) if when else None
    except ValueError:
        return {"error": "Invalid time format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."}
    
    sats = get_visible_satellites(lat, lon, alt, when=dt)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "location": {
            "lat": lat,
            "lon": lon,
            "alt": alt
        },
        "visible_satellites": sats
    }