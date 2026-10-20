import inspect

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.astronomy_service import get_astronomy_data
from app.services.events_service import upcoming_events
from app.utils.deps import get_db

router = APIRouter(prefix="/events", tags=["Events"])


async def _maybe_await(v):
    return await v if inspect.isawaitable(v) else v


@router.get("/night-sky")
async def night_sky_events(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                           db: AsyncSession = Depends(get_db)):
    astronomy = await _maybe_await(get_astronomy_data(lat, lon))
    events = await upcoming_events(db, lat, days=60, limit=5, only_visible=True)
    weather = None
    try:
        from app.utils.astronomy import get_visibility_forecast
        weather = await _maybe_await(get_visibility_forecast(lat, lon))
    except Exception:
        weather = None
    return {"astronomy": astronomy, "upcoming_events": events, "weather": weather,
            "weather_available": weather is not None}