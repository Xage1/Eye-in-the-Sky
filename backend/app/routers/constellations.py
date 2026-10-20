from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.services.constellation_service import visible_constellations

router = APIRouter(prefix="/constellations", tags=["Constellations"])


@router.get("/")
async def constellation_info(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180)):
    return await run_in_threadpool(visible_constellations, lat, lon)