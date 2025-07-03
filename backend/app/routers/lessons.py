from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonOut
from app.database import SessionLocal

router = APIRouter(prefix="/lessons", tags=["Lessons"])

def get_db(): ...
    
@router.get("/", response_model=list[LessonOut])
async def get_lessons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson))
    return result.scalars().all()