import inspect, json, sys
from datetime import datetime, timezone
from app.controllers import skyController as sc

print("##### MODULE HEAD")
src = inspect.getsource(sc).splitlines()
print("\n".join(l for l in src[:90] if len(l) < 200))

for name in ("get_visible_stars", "get_planet_positions", "get_iss_position", "get_visible_satellites"):
    print(f"\n##### {name}")
    print("\n".join(l for l in inspect.getsource(getattr(sc, name)).splitlines() if len(l) < 200))

# helpers the star path relies on
for name in dir(sc):
    if name.startswith("_") and callable(getattr(sc, name)) and any(k in name.lower() for k in ("star", "catalog", "project", "altaz", "screen", "load")):
        print(f"\n##### helper {name}")
        print("\n".join(l for l in inspect.getsource(getattr(sc, name)).splitlines() if len(l) < 200))

print("\n##### SAMPLE OUTPUTS")
when = datetime.now(timezone.utc)
print("planets:", json.dumps(sc.get_planet_positions(-1.2921, 36.8219, when, 90.0, 45.0, 0.0, 1080, 1920, 60.0, 110.0)[:2], default=str)[:600])
import asyncio
print("iss:", json.dumps(asyncio.run(sc.get_iss_position(-1.2921, 36.8219, when)), default=str)[:600])
print("sats:", json.dumps(sc.get_visible_satellites(-1.2921, 36.8219, alt_m=0.0, when=when, limit=2), default=str)[:600])