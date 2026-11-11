"""
Runs the periodic jobs inside the API process, so one small container can replace
API + Celery worker + Celery beat on a low-memory host.

Jobs call the same task functions Celery would, directly (no broker needed).
"""
import importlib
import logging
import threading
import time

logger = logging.getLogger("eyesky.lite")

# (label, first delay s, interval s, module, function)
JOBS = [
    ("tle-refresh", 60, 6 * 3600, "app.tasks.tle_tasks", "fetch_and_store_tle"),
    ("weather-refresh", 120, 3 * 3600, "app.tasks.weather_tasks", "refresh_visibility_scores"),
    ("expire-subscriptions", 90, 6 * 3600, "app.tasks.subscription_tasks", "expire_subscriptions"),
]

_started = False


def _run_forever(label, first, every, module, func):
    time.sleep(first)
    while True:
        t0 = time.time()
        try:
            fn = getattr(importlib.import_module(module), func)
            result = fn()
            logger.info("lite job %s ok: %s (%.1fs)", label, result, time.time() - t0)
        except BaseException as exc:  # includes celery Retry when called outside a worker
            logger.warning("lite job %s failed: %s", label, exc)
        time.sleep(every)


def start_all():
    global _started
    if _started:
        return
    _started = True
    for label, first, every, module, func in JOBS:
        threading.Thread(target=_run_forever, args=(label, first, every, module, func),
                         name="lite-" + label, daemon=True).start()
    logger.info("lite scheduler started: %d jobs", len(JOBS))
