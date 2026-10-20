import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.quiz import QuizQuestion
from app.models.quiz_answer import QuizAnswer
from app.models.quiz_submission import QuizSubmission
from app.models.user import User
from app.schemas.quiz_submission import QuizSubmissionCreate, QuizSubmissionOut
from app.utils.deps import get_current_user, get_db

router = APIRouter(prefix="/quiz", tags=["Quiz"])


async def _load_submission(db: AsyncSession, submission_id: int) -> QuizSubmission:
    result = await db.execute(
        select(QuizSubmission)
        .options(selectinload(QuizSubmission.answers))
        .where(QuizSubmission.id == submission_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


# GET /quiz/  (never includes the correct answer)
@router.get("/")
async def get_questions(
    difficulty: str = "simple",
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
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
    current_user: User = Depends(get_current_user),
):
    if not submission.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    ids = [a.question_id for a in submission.answers]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=400, detail="Duplicate question_id in submission")

    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id.in_(ids)))
    questions = {q.id: q for q in result.scalars().all()}
    missing = [i for i in ids if i not in questions]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown question ids: {missing}")

    # Score on the server, using the stored answer key.
    score = sum(
        1
        for a in submission.answers
        if a.selected_answer.strip().lower() == questions[a.question_id].correct_answer.strip().lower()
    )

    new_submission = QuizSubmission(
        user_id=current_user.id,
        score=score,
        total_questions=len(submission.answers),
    )
    db.add(new_submission)
    await db.flush()

    for a in submission.answers:
        db.add(QuizAnswer(
            submission_id=new_submission.id,
            question_id=a.question_id,
            selected_answer=a.selected_answer,
            correct_answer=questions[a.question_id].correct_answer,
        ))

    await db.commit()
    return await _load_submission(db, new_submission.id)


@router.get("/history", response_model=list[QuizSubmissionOut])
async def get_quiz_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QuizSubmission)
        .options(selectinload(QuizSubmission.answers))
        .where(QuizSubmission.user_id == current_user.id)
        .order_by(QuizSubmission.timestamp.desc())
    )
    return result.scalars().all()