from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, nullable=False)
    options = Column(Text, nullable=False)  # JSON string
    correct_answer = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # "simple", "complex"
    topic = Column(String, nullable=True)        # "planets", "stars", etc.