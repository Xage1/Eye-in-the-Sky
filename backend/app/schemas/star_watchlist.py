from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StarWatchCreate(BaseModel):
    star_name: str
    constellation: Optional[str] = None
    description: Optional[str] = None  # ✅ Included

class StarWatchOut(StarWatchCreate):
    id: int
    user_id: int
    added_on: datetime

    class Config:
        orm_mode = True