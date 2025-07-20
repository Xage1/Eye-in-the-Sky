from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dark_mode = Column(Boolean, default=False)
    default_difficulty = Column(String, default="simple")
    notifications_enabled = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")