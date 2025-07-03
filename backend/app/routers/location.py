from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.database import SessionLocal
from app.models.location import LocationEntry
from app.schemas.location import LocationCreate, LocationOut
from app.utils.geo import reverse_geocode
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/location", tags=["Location"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Store user's geolocation
@router.post("/store", response_model=LocationOut)
async def store_location(
    location: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    city, country = await reverse_geocode(location.latitude, location.longitude)
    
    entry = LocationEntry(
        latitude=location.latitude,
        longitude=location.longitude,
        city=city,
        country=country,
        timestamp=datetime.utcnow().isoformat(),
        user_id=current_user.id
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

# ✅ Get location history for current user
@router.get("/history", response_model=list[LocationOut])
async def get_location_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(LocationEntry).where(LocationEntry.user_id == current_user.id).order_by(LocationEntry.timestamp.desc()).limit(20)
    )
    return result.scalars().all()
