"""
app/schemas/notification.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    solar_event_id: Optional[int] = None
    title: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    unread_count: int
