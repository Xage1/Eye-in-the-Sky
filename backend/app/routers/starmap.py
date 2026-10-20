from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.services.constellation_service import evening_time, visible_constellations

router = APIRouter(prefix="/starmap", tags=["Star Map"])


@router.get("/")
async def starmap(lat: float = Query(..., ge=-90, le=90, description="Observer latitude"),
                  lon: float = Query(..., ge=-180, le=180, description="Observer longitude"),
                  date: Optional[str] = Query(None, description="YYYY-MM-DD; shows 20:00 local solar time")):
    when = None
    if date:
        try:
            when = evening_time(lon, date)
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    data = await run_in_threadpool(visible_constellations, lat, lon, when)
    return {"observer": {"lat": lat, "lon": lon}, **data}