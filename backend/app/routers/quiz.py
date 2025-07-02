from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.quiz import QuizSubmit
from app.database import SessionLocal
from app.models.quiz import QuizQuestion
import json

router = APIRouter(prefix="/quiz", tags=["Quiz"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
async def get_questions(difficulty: str = "simple", db: AsyncSession = Depends(get_db)):
    result = await db.execute(f"SELECT * FROM quiz_questions WHERE difficulty = '{difficulty}' LIMIT 5")
    rows = result.fetchall()
    return [
        {
            "id": row.id,
            "question_text": row.question_text,
            "options": json.loads(row.options)
        } for row in rows
    ]

@router.post("/submit")
async def submit_quiz(submit: QuizSubmit):
    score = sum(1 for q in submit.answers if q.answer == q.correct)
    return {"score": score, "total": len(submit.answers)}