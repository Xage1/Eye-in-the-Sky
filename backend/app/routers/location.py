from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal
from app.models.location import LocationEntry
from app.schemas.location import LocationCreate
from app.utils.geo import reverse_geocode
from datetime import datetime

router = APIRouter(prefix="/location", tags=["Location"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/store")
async def store_location(location: LocationCreate, db: AsyncSession = Depends(get_db)):
    city, country = await reverse_geocode(location.latitude, location.longitude)
    entry = LocationEntry(
        latitude=location.latitude,
        longitude=location.longitude,
        city=city,
        country=country,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

@router.get("/history")
async def get_location_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute("SELECT * FROM location_entries ORDER BY timestamp DESC LIMIT 20")
    return [dict(r._mapping) for r in result.fetchall()]