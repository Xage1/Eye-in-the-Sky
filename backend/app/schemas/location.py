from pydantic import BaseModel
from typing import Optional

class LocationCreate(BaseModel):
    latitude: float
    longitude: float

class LocationOut(LocationCreate):
    id: int
    city: Optional[str] = None
    country: Optional[str] = None
    timestamp: Optional[str] = None
    user_id: int
    model_config = {"from_attributes": True}