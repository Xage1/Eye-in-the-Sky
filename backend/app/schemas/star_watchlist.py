from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StarWatchCreate(BaseModel):
    star_name: str = Field(..., min_length=1)
    constellation: str = Field(..., min_length=1)
    description: str | None = None

class StarWatchOut(StarWatchCreate):
    id: int
    user_id: int
    added_on: datetime

    class Config:
        orm_mode = True