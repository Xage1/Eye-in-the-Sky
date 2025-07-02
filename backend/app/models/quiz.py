from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text)
    difficulty = Column(String)
    options = Column(Text)  # JSON string
    correct_option = Column(String)