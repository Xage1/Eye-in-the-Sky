from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LocationCreate(BaseModel):
    latitude: float
    longitude: float


class LocationOut(LocationCreate):
    id: int
    city: Optional[str] = None
    country: Optional[str] = None
    visibility_score: Optional[int] = None
    visibility_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    user_id: int
    model_config = {"from_attributes": True}
