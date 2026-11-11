import asyncio, time
from datetime import datetime, timezone
from app.controllers import skyController as sc

lat, lon, az, alt, roll = -1.2921, 36.8219, 90.0, 45.0, 0.0
W, H, FH, FV = 1080, 1920, 60.0, 110.0
when = datetime.now(timezone.utc)

def t(label, fn):
    for run in (1, 2):
        s = time.perf_counter()
        try:
            r = fn()
            if asyncio.iscoroutine(r):
                r = asyncio.run(r)
            n = len(r) if hasattr(r, "__len__") else "-"
            status = f"ok ({n})"
        except Exception as e:
            status = f"ERR {type(e).__name__}: {str(e)[:80]}"
        print(f"{label:14s} run{run}: {(time.perf_counter()-s)*1000:8.0f} ms  {status}")

t("stars", lambda: sc.get_visible_stars(lat, lon, when, az, alt, roll, W, H, FH, FV, mag_limit=sc._DEFAULT_MAG_LIMIT))
t("constellation", lambda: sc.get_closest_constellation(lat, lon, when, az, alt))
t("planets", lambda: sc.get_planet_positions(lat, lon, when, az, alt, roll, W, H, FH, FV))
t("moon", lambda: sc.get_moon_phase_local(when))
t("iss", lambda: sc.get_iss_position(lat, lon, when))
t("satellites", lambda: sc.get_visible_satellites(lat, lon, alt_m=0.0, when=when, limit=15))