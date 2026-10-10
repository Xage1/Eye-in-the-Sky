"""
app/routers/notifications.py

In-app notification feed for celestial event alerts (and future alert
types). Available to every authenticated user -- no Pro gate, since
event alerts are a core engagement feature, not the premium JWST
pipeline.

Endpoints:
  GET   /notifications              - list current user notifications, newest first
  GET   /notifications/unread-count - badge count for the frontend
  PATCH /notifications/read-all     - mark all notifications read
  PATCH /notifications/{id}/read    - mark one notification read
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationOut, UnreadCountOut
from app.utils.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    return {"unread_count": result.scalar_one()}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    unread = result.scalars().all()
    for n in unread:
        n.is_read = True
    await db.commit()
    return {"marked_read": len(unread)}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")
    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return notif
