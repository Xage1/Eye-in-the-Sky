"""app/models/quote.py — Astronomer quotes"""
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, func
from app.database import Base

class AstronomerQuote(Base):
    __tablename__ = "astronomer_quotes"
    id          = Column(Integer, primary_key=True, index=True)
    quote       = Column(Text, nullable=False)
    astronomer  = Column(String(150), nullable=False)
    birth_year  = Column(Integer, nullable=True)
    death_year  = Column(Integer, nullable=True)
    nationality = Column(String(100), nullable=True)
    context     = Column(Text, nullable=True)
    category    = Column(String(80), nullable=True)
    featured    = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())