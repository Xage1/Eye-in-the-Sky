from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String)
    difficulty = Column(String, nullable=False)
