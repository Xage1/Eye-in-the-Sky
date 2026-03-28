from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StarWatchCreate(BaseModel):
    star_name: str = Field(..., min_length=1)
    description: Optional[str] = None

class StarWatchOut(StarWatchCreate):
    id: int
    user_id: int
    star_name: str
    description: Optional[str] = None
    constellation: Optional[str] = None
    added_at: Optional[datetime] = None
    model_config = {"from_attributes": True}