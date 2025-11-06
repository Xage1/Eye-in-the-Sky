from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from app.services.satellite_service import get_visible_satellites

router = APIRouter(prefix="/sky", tags=["Satellites"])

@router.get("/satellites/visible")
def satellites_visible(
    lat: float = Query(...),
    lon: float = Query(...),
    alt: Optional[float] = 0.0,
    limit: Optional[int] = 10,
    when: Optional[str] = None
):
    when_dt = datetime.fromisoformat(when) if when else None
    sats = get_visible_satellites(lat, lon, alt, when=when_dt, limit=limit)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "location": {"lat": lat, "lon": lon, "alt": alt},
        "visible_satellites": sats
    }