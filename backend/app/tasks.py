from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import SessionLocal, Event
from .utils import send_email_notification

celery = Celery(__name__, broker='redis://localhost:6379/0')

@celery.task(bind=True, default_retry_delay=60, max_retries=3)
def check_and_notify_users(self):
    db: Session = SessionLocal()
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        events = db.query(Event).filter(Event.date == tomorrow.date()).all()
        
        for event in events:
            send_email_notification(event)

    except Exception as exc:
        self.retry(exc=exc)
    finally:
        db.close()

celery.conf.beat_schedule = {
    'check-and-notify-everyday': {
        'task': 'app.tasks.check_and_notify_users',
        'schedule': timedelta(days=1),
    },
}