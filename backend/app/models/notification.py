"""
app/models/notification.py

In-app notification feed. Populated by the Celery beat task
(check_upcoming_events) when a SolarEvent peak falls within the next
48 hours and the user is opted in. Generic enough to carry other
alert types later (solar_event_id is nullable).
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "solar_event_id", name="uq_notification_user_event"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    solar_event_id = Column(Integer, ForeignKey("solar_events.id"), nullable=True)

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    solar_event = relationship("SolarEvent")
