"""
app/utils/redis_client.py

Single shared Redis client for the API and Celery worker processes.
Uses the same REDIS_URL env var as app/worker.py so both processes
connect identically.
"""

import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client
