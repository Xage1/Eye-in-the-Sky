"""Subscription housekeeping: mark lapsed paid periods as expired (runs daily from beat)."""
import logging
import os

from sqlalchemy import create_engine, text

from app.worker import celery_app

logger = logging.getLogger(__name__)


def _sync_url() -> str:
    url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
    return url.replace("+asyncpg", "")


@celery_app.task(name="app.tasks.subscription_tasks.expire_subscriptions")
def expire_subscriptions() -> dict:
    engine = create_engine(_sync_url(), pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            res = conn.execute(text(
                "UPDATE user_subscriptions SET status='expired', plan='free' "
                "WHERE status='active' AND current_period_end IS NOT NULL AND current_period_end < now()"
            ))
            n = res.rowcount or 0
    finally:
        engine.dispose()
    logger.info("expire_subscriptions: %s expired", n)
    return {"expired": n}
