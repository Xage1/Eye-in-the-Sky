from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.events_service import upcoming_events
from app.utils.deps import get_db

router = APIRouter(prefix="/events", tags=["Celestial Events"])


@router.get("/")
async def events(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                 days: int = Query(120, ge=1, le=730), limit: int = Query(20, ge=1, le=100),
                 event_type: Optional[str] = None, only_visible: bool = False,
                 db: AsyncSession = Depends(get_db)):
    items = await upcoming_events(db, lat, days, limit, event_type, only_visible)
    return {"observer": {"lat": lat, "lon": lon}, "days": days, "count": len(items), "events": items}