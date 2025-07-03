from pydantic import BaseModel
from typing import Optional

class LocationCreate(BaseModel):
    latitude: float
    longitude: float

class LocationOut(LocationCreate):
    id: int
    city: Optional[str]
    country: Optional[str]
    timestamp: str
    user_id: int

    class Config:
        orm_mode = True
