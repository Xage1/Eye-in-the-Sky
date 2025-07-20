from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("quiz_submissions.id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    selected_answer = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)

    submission = relationship("QuizSubmission", back_populates="answers")
