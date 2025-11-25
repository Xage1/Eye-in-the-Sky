from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LessonCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    difficulty: Optional[str] = "Medium"

class LessonOut(LessonCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
