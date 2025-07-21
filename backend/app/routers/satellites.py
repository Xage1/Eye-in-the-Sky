from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.satellite_service import get_visible_satellites

router = APIRouter(prefix="/sky", tags=["Sky Analysis"])

class SatelliteRequest(BaseModel):
    latitude: float
    longitude: float
    altitude: float = 0  # Optional, default is sea level

@router.post("/satellites/visible")
async def satellites_visible(req: SatelliteRequest):
    try:
        data = await get_visible_satellites(req.latitude, req.longitude, req.altitude)
        return {"visible_satellites": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))