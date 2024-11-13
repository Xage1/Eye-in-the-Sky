import smtplib
from email.message import EmailMessage
from astropy.time import Time
from astropy.coordinates import get_sun, EarthLocation

def send_email_notification(event):
    msg = EmailMessage()
    msg['Subject'] = f'Upcoming Astronomical Event: {event.name}'
    msg['From'] = "your_email@example.com"
    msg['To'] = "user_email@example.com"  # User's email here

    msg.set_content(f"Event {event.name} is happening on {event.date} at {event.time}!")

    with smtplib.SMTP("smtp.example.com", 587) as server:
        server.starttls()
        server.login("your_email@example.com", "your_password")
        server.send_message(msg)


def calculate_event_visibility(latitude, longitude):
    location = EarthLocation(lat=latitude, lon=longitude)
    # Use Astropy to determine if the event is visible at this location
    # Return data for frontend display
    pass