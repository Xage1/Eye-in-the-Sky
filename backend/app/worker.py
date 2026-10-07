"""
app/worker.py -- Celery application for Eye in the Sky

Background queues:
  default         -- general async tasks
  tle_refresh     -- fetch fresh TLE data from Celestrak every 6 hours
  alerts          -- push notifications for upcoming celestial events
  jwst_processing -- download + visualize JWST FITS mosaics (large, slow)
"""

import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "eyesky",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.tle_tasks",
        "app.tasks.event_tasks",
        "app.tasks.weather_tasks",
        "app.tasks.jwst_tasks",
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
        "app.tasks.jwst_tasks.*": {"queue": "jwst_processing"},
    },
)

celery_app.conf.beat_schedule = {
    "refresh-tle-every-6h": {
        "task": "app.tasks.tle_tasks.fetch_and_store_tle",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "check-celestial-events-daily": {
        "task": "app.tasks.event_tasks.check_upcoming_events",
        "schedule": crontab(minute=0, hour=0),
    },
    "refresh-weather-every-3h": {
        "task": "app.tasks.weather_tasks.refresh_visibility_scores",
        "schedule": crontab(minute=0, hour="*/3"),
    },
}

app = celery_app
