"""
app/worker.py — Celery application for Eye in the Sky
 
Background queues:
  default       — general async tasks
  tle_refresh   — fetch fresh TLE data from Celestrak every 6 hours
  alerts        — push notifications for upcoming celestial events
"""

import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# ── Celery app ────────────────────────────────────────────────
celery_app = Celery(
    "eyesky",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.tle_tasks",
        "app.tasks.event_tasks",
        "app.tasks.weather_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.tle_tasks.*": {"queue": "tle_refresh"},
        "app.tasks.event_tasks*": {"queue": "alerts"},
        "app.tasks.weather_tasks*": {"queue": "default"},
    },
)

# ── Periodic schedule (Celery Beat) ──────────────────────────
celery_app.conf.beat_schedule = {
    # Refresh TLE satellite data every 6 hours
    "refresh-tle-every-6h": {
        "task": "app.tasks.tle_tasks.fetch_and_store_tle",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Check for upcoming celestial events daily at midnight UTC
    "check-celestial-events-daily": {
        "task": "app.tasks.event_tasks.check_upcoming_events",
        "schedule": crontab(minute=0, hour=0),
    },
    # Refresh weather / visibility scores every 3 hours
    "refresh-weather-every-3h": {
        "task": "app.tasks.weather_tasks.refresh_visibility_scores",
        "schedule": crontab(minute=0, hour="*/3"),
    },
}
 
# Alias so `celery -A app.worker` works
app = celery_app