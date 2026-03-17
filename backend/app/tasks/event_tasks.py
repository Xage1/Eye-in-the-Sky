"""
app/tasks/event_tasks.py
Checks for upcoming celestial events and queues push notifications.
Runs daily at midnight UTC via Celery Beat.
"""

import logging
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.event_tasks.check_upcoming_events",
    bind=True,
    max_retries=3,
    default_retry_delay=600,
)
def check_upcoming_events(self):
    """
    Queries the events table for items in the next 48 hours
    and dispatches push notification tasks for opted-in users.
    Stub — full implementation once events service and push tokens are wired up.
    """
    try:
        logger.info("Event check: scanning for upcoming celestial events ...")
        # TODO: query DB for events within 48h, dispatch per-user notifications
        return {"status": "ok", "events_checked": 0}
    except Exception as exc:
        logger.error(f"Event check failed: {exc}")
        raise self.retry(exc=exc)