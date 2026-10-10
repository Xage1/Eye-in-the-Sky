"""
app/tasks/event_tasks.py

Checks for upcoming celestial events (meteor showers, eclipses, etc.)
and creates in-app notifications for opted-in users whose saved
locations fall within the event visibility latitude range.

Runs daily at midnight UTC via Celery Beat (see app/worker.py).
Idempotent: a user is never notified twice for the same event, enforced
by the (user_id, solar_event_id) unique constraint on notifications.
"""

import logging
from datetime import datetime, timedelta

from app.worker import celery_app
from app.utils.sync_db import get_sync_session
from app.models.solar_event import SolarEvent
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)

ALERT_WINDOW_HOURS = 48


def _user_opted_in(user: User) -> bool:
    return user.settings is None or user.settings.notifications_enabled


def _user_can_see_event(event: SolarEvent, user: User) -> bool:
    """
    True if the event has no latitude restriction, the user has no saved
    locations to check against (cannot filter, so do not block the alert),
    or at least one saved location falls within the event visible range.
    """
    if event.min_latitude is None and event.max_latitude is None:
        return True
    if not user.locations:
        return True
    lo = event.min_latitude if event.min_latitude is not None else -90.0
    hi = event.max_latitude if event.max_latitude is not None else 90.0
    return any(lo <= loc.latitude <= hi for loc in user.locations)


@celery_app.task(
    name="app.tasks.event_tasks.check_upcoming_events",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
)
def check_upcoming_events(self):
    db = get_sync_session()
    try:
        now = datetime.utcnow()
        window_end = now + timedelta(hours=ALERT_WINDOW_HOURS)

        events = (
            db.query(SolarEvent)
            .filter(
                SolarEvent.is_upcoming.is_(True),
                SolarEvent.start_time <= window_end,
            )
            .filter(
                (SolarEvent.end_time.is_(None)) | (SolarEvent.end_time >= now)
            )
            .all()
        )

        if not events:
            logger.info("Event check: no events in the next %sh window", ALERT_WINDOW_HOURS)
            return {"status": "ok", "events_checked": 0, "notifications_created": 0}

        users = db.query(User).filter(User.is_active.is_(True)).all()

        created = 0
        for event in events:
            when = event.peak_time or event.start_time
            for user in users:
                if not _user_opted_in(user):
                    continue

                existing = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user.id,
                        Notification.solar_event_id == event.id,
                    )
                    .first()
                )
                if existing:
                    continue

                if not _user_can_see_event(event, user):
                    continue

                notif = Notification(
                    user_id=user.id,
                    solar_event_id=event.id,
                    title=f"{event.event_type.replace(\x27_\x27, \x27 \x27).title()}: {event.name}",
                    message=(
                        f"{event.name} peaks around {when:%b %d, %Y %H:%M} UTC. "
                        + (event.description or "")
                    ).strip(),
                )
                db.add(notif)
                created += 1

        db.commit()
        logger.info(
            "Event check: %s events scanned, %s notifications created",
            len(events), created,
        )
        return {"status": "ok", "events_checked": len(events), "notifications_created": created}
    except Exception as exc:
        db.rollback()
        logger.error(f"Event check failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
