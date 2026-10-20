import asyncio, math, time
from datetime import datetime, timezone
from app.controllers import skyController as sc
from app.utils import sky_tools

lat, lon, az, alt, roll = -1.2921, 36.8219, 90.0, 45.0, 0.0
when = datetime.now(timezone.utc)
A = (lat, lon, when, az, alt, roll, 1080, 1920, 60.0, 110.0)

def dang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)

def timed(label, fn, n=3):
    ts = []
    for _ in range(n):
        s = time.perf_counter(); r = fn()
        if asyncio.iscoroutine(r): r = asyncio.run(r)
        ts.append((time.perf_counter() - s) * 1000)
    print(f"{label:12s} " + "  ".join(f"{x:7.1f} ms" for x in ts))
    return r

print("== stars")
new = sc.get_visible_stars(*A)
ref = sky_tools.find_nearby_stars(lat, lon, azimuth=az, altitude=alt, radius=40.0, when=when, limit=5000)
refm = {s["hr"]: s for s in ref}
d_alt = d_az = 0.0; common = 0
for s in new:
    r = refm.get(s["hr"])
    if r:
        common += 1
        d_alt = max(d_alt, abs(s["altitude_deg"] - r["altitude_deg"]))
        d_az = max(d_az, dang(s["azimuth_deg"], r["azimuth_deg"]))
print(f"new={len(new)} stars in view; matched {common} against sky_tools; max diff alt={d_alt:.3f} deg az={d_az:.3f} deg")
print("brightest:", [(s["name"], s["bayer"], s["magnitude"], s["screen_x"], s["screen_y"]) for s in new[:4]])

print("== planets")
n = {p["name"]: p for p in sc.get_planet_positions(*A)}
o = {p["name"]: p for p in sc._orig_get_planet_positions(*A)}
for k in sorted(set(n) | set(o)):
    if k in n and k in o:
        print(f"{k:8s} d_alt={abs(n[k]['altitude_deg']-o[k]['altitude_deg']):.3f} d_az={dang(n[k]['azimuth_deg'], o[k]['azimuth_deg']):.3f}")
    else:
        print(f"{k:8s} only in {'new' if k in n else 'old'}")

print("== satellites")
n = sc.get_visible_satellites(lat, lon, 0.0, when, 5000)
o = {s["name"]: s for s in sc._orig_get_visible_satellites(lat, lon, 0.0, when, 5000)}
mx_alt = mx_az = 0.0; c = 0
for s in n:
    r = o.get(s["name"])
    if r:
        c += 1; mx_alt = max(mx_alt, abs(s["altitude_deg"] - r["altitude_deg"])); mx_az = max(mx_az, dang(s["azimuth_deg"], r["azimuth_deg"]))
print(f"new={len(n)} above horizon, old={len(o)}; matched {c}; max diff alt={mx_alt:.3f} deg az={mx_az:.3f} deg")

print("== iss")
print(asyncio.run(sc.get_iss_position(lat, lon, when)))

print("== timings (3 calls each)")
timed("stars", lambda: sc.get_visible_stars(*A))
timed("planets", lambda: sc.get_planet_positions(*A))
timed("satellites", lambda: sc.get_visible_satellites(lat, lon, alt_m=0.0, when=when, limit=15))
timed("iss", lambda: sc.get_iss_position(lat, lon, when))