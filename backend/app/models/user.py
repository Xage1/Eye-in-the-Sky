from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base
from sqlalchemy.orm import relationship, declarative_base
from app.models.user_settings import UserSettings

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Existing relationship
    locations = relationship("Location", back_populates="user", cascade="all")

    # One-to-one relationship for settings
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all",
        lazy="selectin"
    )

    star_watchlist = relationship("StarWatchlist", back_populates="user", cascade="all")