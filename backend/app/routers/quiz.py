from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.quiz import QuizQuestion
from app.schemas.quiz import QuizSubmit, QuizAnswer
import json

router = APIRouter(prefix="/quiz", tags=["Quiz"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ GET /quiz/
@router.get("/")
async def get_questions(
    difficulty: str = "simple",
    topic: str = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(QuizQuestion).where(QuizQuestion.difficulty == difficulty)
    if topic:
        stmt = stmt.where(QuizQuestion.topic == topic)
    stmt = stmt.order_by(func.random()).limit(5)

    result = await db.execute(stmt)
    questions = result.scalars().all()

    return [
        {
            "id": q.id,
            "question_text": q.question_text,
            "options": json.loads(q.options),
        }
        for q in questions
    ]

# ✅ POST /quiz/submit
@router.post("/submit")
async def submit_quiz(submit: QuizSubmit, db: AsyncSession = Depends(get_db)):
    ids = [q.id for q in submit.answers]
    stmt = select(QuizQuestion).where(QuizQuestion.id.in_(ids))
    result = await db.execute(stmt)
    questions_dict = {q.id: q.correct_answer for q in result.scalars().all()}

    score = 0
    for a in submit.answers:
        correct = questions_dict.get(a.id)
        if correct and a.answer.strip().lower() == correct.strip().lower():
            score += 1

    return {"score": score, "total": len(submit.answers)}