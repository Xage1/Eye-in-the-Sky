# app/routers/lessons.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.database import SessionLocal
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonOut
from app.utils.deps import get_db  # you have get_db pattern in deps.py

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.get("/", response_model=List[LessonOut])
async def get_lessons(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    db: AsyncSession = Depends(get_db)
):
    q = select(Lesson)
    if category:
        q = q.where(Lesson.category == category)
    if difficulty:
        q = q.where(Lesson.difficulty == difficulty)
    result = await db.execute(q.order_by(Lesson.id))
    return result.scalars().all()


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.post("/", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(payload: LessonCreate, db: AsyncSession = Depends(get_db)):
    new = Lesson(**payload.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


@router.get("/by-category/{category}", response_model=List[LessonOut])
async def lessons_by_category(category: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.category == category).order_by(Lesson.id))
    return result.scalars().all()