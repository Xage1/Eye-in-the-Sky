from pydantic import BaseModel
from typing import List

class Answer(BaseModel):
    question_id: int
    answer: str
    correct: str

class QuizSubmit(BaseModel):
    answers: List[Answer]