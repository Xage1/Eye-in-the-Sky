"""
app/routers/location.py

Lets a user save their observing locations (reverse-geocoded to a
city/country label) and list their history. These are the locations
the celestial-events alert task and the visibility-score refresh task
both read from.

Endpoints:
  POST /location/store   - save a new location for the current user
  GET  /location/history - list the current user own saved locations
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.location import Location
from app.schemas.location import LocationCreate, LocationOut
from app.utils.geo import reverse_geocode
from app.utils.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("/store", response_model=LocationOut)
async def store_location(
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    city, country = await reverse_geocode(location.latitude, location.longitude)

    entry = Location(
        latitude=location.latitude,
        longitude=location.longitude,
        city=city,
        country=country,
        user_id=current_user.id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/history", response_model=list[LocationOut])
async def get_location_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Location)
        .where(Location.user_id == current_user.id)
        .order_by(Location.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()
