from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StarWatchCreate(BaseModel):
    star_name: str = Field(..., min_length=1)
    description: str | None = None

class StarWatchOut(StarWatchCreate):
    id: int
    user_id: int
    star_name: str
    description: Optional[str] = None
    added_at: datetime

    class Config:
        orm_mode = True