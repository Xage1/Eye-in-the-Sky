"""
app/utils/sync_db.py

Synchronous SQLAlchemy session for use inside Celery tasks.
Celery workers run synchronously and cannot use the async SessionLocal
from app.database (which requires an event loop). This uses the same
DATABASE_URL_SYNC env var Alembic uses, but reads it at call time so it
picks up the container's value (postgres:5432), not the host's.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_sync_engine = None
_SyncSessionLocal = None


def get_sync_session():
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        db_url = os.getenv("DATABASE_URL_SYNC")
        if not db_url:
            raise RuntimeError("DATABASE_URL_SYNC is not set")
        _sync_engine = create_engine(db_url, pool_pre_ping=True)
        _SyncSessionLocal = sessionmaker(bind=_sync_engine)
    return _SyncSessionLocal()
