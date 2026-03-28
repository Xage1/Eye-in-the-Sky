from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuizAnswerIn(BaseModel):
    question_id: int
    selected_answer: str
    correct_answer: str

class QuizSubmissionCreate(BaseModel):
    answers: List[QuizAnswerIn]

class QuizAnswerOut(QuizAnswerIn):
    id: int
    model_config = {"from_attributes": True}

class QuizSubmissionOut(BaseModel):
    id: int
    user_id: int
    timestamp: Optional[datetime] = None
    score: int
    total_questions: int
    answers: List[QuizAnswerOut] = []
    model_config = {"from_attributes": True}