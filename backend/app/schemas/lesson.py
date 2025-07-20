from pydantic import BaseModel

class LessonCreate(BaseModel):
    title: str
    content: str
    category: str

class LessonOut(LessonCreate):
    id: int

    class Config:
        orm_mode = True
