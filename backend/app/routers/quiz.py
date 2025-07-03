from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.quiz import QuizQuestion
from app.models.quiz_answer import QuizAnswer
from models.quiz_submission import QuizSubmission
from app.schemas.quiz_submission import QuizSubmissionOut, QuizSubmissionCreate
from app.schemas.quiz import QuizSubmit, QuizAnswer
from app.utils.deps import get_current_user
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



@router.post("/submit", response_model=QuizSubmissionOut)
async def submit_quiz(
    submission: QuizSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = len(submission.answers)
    score = sum(1 for ans in submission.answers if ans.selected_answer.lower() == ans.correct_answer.lower())

    new_submission = QuizSubmission(
        user_id=current_user.id,
        score=score,
        total_questions=total
    )
    db.add(new_submission)
    await db.flush()  # Get new_submission.id

    for ans in submission.answers:
        db.add(QuizAnswer(
            submission_id=new_submission.id,
            question_id=ans.question_id,
            selected_answer=ans.selected_answer,
            correct_answer=ans.correct_answer
        ))

    await db.commit()
    await db.refresh(new_submission)
    return new_submission


@router.get("/history", response_model=list[QuizSubmissionOut])
async def get_quiz_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(QuizSubmission).where(QuizSubmission.user_id == current_user.id)
    )
    return result.scalars().all()


