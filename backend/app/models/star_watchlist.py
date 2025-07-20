from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base


class StarWatchlist(Base):
    __tablename__ = "star_watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    star_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Assuming a User model exists
    user = relationship("User", back_populates="star_watchlist")  # Back reference to User model