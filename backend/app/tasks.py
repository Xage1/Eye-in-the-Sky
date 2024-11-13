from celery import Celery
from datetime import datetime, timedelta
from .models import SessionLocal, Event
from .utils import send_email_notification

celery = Celery(__name__, broker='redis://localhost:6379/0')

@celery.task
def check_and_notify_users():
    db = SessionLocal()
    # Get events happening in the next 24 hours
    tomorrow = datetime.now() + timedelta(days=1)
    events = db.query(Event).filter(Event.date == tomorrow.date()).all()
    
    for event in events:
        # Notify users subscribed to this event type or location
        send_email_notification(event)

    db.close()

# Schedule task daily at a specific time
celery.conf.beat_schedule = {
    'check-and-notify-everyday': {
        'task': 'check_and_notify_users',
        'schedule': timedelta(days=1),
    },
}