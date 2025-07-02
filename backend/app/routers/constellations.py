from fastapi import APIRouter, Query
from app.utils.astronomy import get_constellation_data

router = APIRouter(prefix="/constellations", tags=["Constellations"])

@router.get("/")
async def constellation_info(lat: float = Query(...), lon: float = Query(...)):
    return await get_constellation_data(lat, lon)