import smtplib
from email.message import EmailMessage
from astropy.coordinates import get_sun, EarthLocation, AltAz
from astropy.time import Time
from datetime import datetime

def send_email_notification(event):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Upcoming Astronomical Event: {event.name}'
        msg['From'] = "your_email@example.com"
        msg['To'] = "user_email@example.com"

        msg.set_content(f"Event {event.name} is happening on {event.date} at {event.time}!")

        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login("your_email@example.com", "your_password")
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def calculate_event_visibility(latitude, longitude, event_time):
    location = EarthLocation(lat=latitude, lon=longitude)
    observing_time = Time(event_time)
    altaz_frame = AltAz(obstime=observing_time, location=location)
    sun_position = get_sun(observing_time).transform_to(altaz_frame)
    is_visible = sun_position.alt.deg < -6  # Check if sun is below the horizon
    return {"is_visible": is_visible}