"""app/utils/ttl_cache.py - tiny async TTL cache for slow external calls (weather)."""
import functools
import time


def async_ttl_cache(ttl: float = 600.0, ndigits: int = 1, maxsize: int = 512):
    """Cache by (lat, lon) rounded to `ndigits` (0.1 deg ~ 11 km). Error results are never cached."""
    def deco(fn):
        store: dict = {}

        @functools.wraps(fn)
        async def wrapper(lat, lon, *args, **kwargs):
            key = (round(float(lat), ndigits), round(float(lon), ndigits), args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            hit = store.get(key)
            if hit is not None and now - hit[0] < ttl:
                return hit[1]
            val = await fn(lat, lon, *args, **kwargs)
            if not (isinstance(val, dict) and "error" in val):
                if len(store) >= maxsize:
                    store.clear()
                store[key] = (now, val)
            return val

        return wrapper
    return deco