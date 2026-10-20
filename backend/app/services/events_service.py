"""app/services/events_service.py - upcoming celestial events from the solar_events table."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.solar_event import SolarEvent


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def _row(e: SolarEvent, lat: Optional[float]) -> dict:
    visible = True
    if lat is not None:
        if e.min_latitude is not None and lat < e.min_latitude:
            visible = False
        if e.max_latitude is not None and lat > e.max_latitude:
            visible = False
    return {
        "id": e.id, "name": e.name, "event_type": e.event_type,
        "description": e.description,
        "start_time": _iso(e.start_time), "peak_time": _iso(e.peak_time), "end_time": _iso(e.end_time),
        "visible_regions": e.visible_regions, "visible_at_location": visible,
        "zhr": e.zhr, "parent_body": e.parent_body, "eclipse_type": e.eclipse_type,
        "magnitude": e.magnitude, "is_notable": bool(e.is_notable),
    }


async def upcoming_events(db: AsyncSession, lat: Optional[float] = None, days: int = 120,
                          limit: int = 20, event_type: Optional[str] = None,
                          only_visible: bool = False) -> list:
    now = datetime.now(timezone.utc)
    last = func.coalesce(SolarEvent.end_time, SolarEvent.peak_time, SolarEvent.start_time)
    q = select(SolarEvent).where(and_(last >= now, SolarEvent.start_time <= now + timedelta(days=days)))
    if event_type:
        q = q.where(func.lower(SolarEvent.event_type) == event_type.lower())
    q = q.order_by(func.coalesce(SolarEvent.peak_time, SolarEvent.start_time)).limit(limit * 3)
    rows = (await db.execute(q)).scalars().all()
    out = [_row(e, lat) for e in rows]
    if only_visible:
        out = [r for r in out if r["visible_at_location"]]
    return out[:limit]