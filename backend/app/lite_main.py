"""
Entry point for small hosts:  uvicorn app.lite_main:app --host 0.0.0.0 --port $PORT --workers 1
Same app as app.main, plus the background jobs.
"""
from app.main import app  # noqa: F401
from app.lite_scheduler import start_all

start_all()
