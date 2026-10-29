"""Satellite / ISS facts: live state, orbit, and the next passes over an observer."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

_A = 6378.137
_E2 = 0.00669437999014
_MU = 398600.4418

ISS_FACTS = [
    ["Launched", "20 November 1998 (first module, Zarya)"],
    ["Continuously crewed since", "2 November 2000"],
    ["Crew", "usually 7 people (3 to 7 over its history)"],
    ["Size", "109 m long by 73 m wide, about a football field"],
    ["Mass", "about 420,000 kg"],
    ["Pressurised volume", "about 916 m³, roughly a Boeing 747 cabin"],
    ["Orbit", "one lap every 92 minutes, so 16 sunrises and 16 sunsets a day"],
    ["Speed", "about 27,600 km/h (7.7 km/s)"],
    ["Partners", "NASA, Roscosmos, ESA, JAXA and CSA"],
    ["Brightness", "often the third brightest object in the night sky after the Moon and Venus"],
    ["Planned retirement", "around 2030, then a controlled descent over the ocean"],
]


def _gmst_rad(jd: np.ndarray) -> np.ndarray:
    return np.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360.0)


def _teme_to_ecef(r: np.ndarray, theta: np.ndarray) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.stack([r[:, 0] * c + r[:, 1] * s, -r[:, 0] * s + r[:, 1] * c, r[:, 2]], axis=1)


def _obs_ecef(lat: float, lon: float, alt_m: float) -> np.ndarray:
    phi, lam = math.radians(lat), math.radians(lon)
    n = _A / math.sqrt(1 - _E2 * math.sin(phi) ** 2)
    h = alt_m / 1000.0
    return np.array([(n + h) * math.cos(phi) * math.cos(lam), (n + h) * math.cos(phi) * math.sin(lam),
                     (n * (1 - _E2) + h) * math.sin(phi)])


def _altaz(vec_ecef: np.ndarray, lat: float, lon: float):
    """Alt/az/range of ECEF positions (relative vector d already subtracted)."""
    phi, lam = math.radians(lat), math.radians(lon)
    d = vec_ecef
    east = -math.sin(lam) * d[:, 0] + math.cos(lam) * d[:, 1]
    north = (-math.sin(phi) * math.cos(lam) * d[:, 0] - math.sin(phi) * math.sin(lam) * d[:, 1] + math.cos(phi) * d[:, 2])
    up = (math.cos(phi) * math.cos(lam) * d[:, 0] + math.cos(phi) * math.sin(lam) * d[:, 1] + math.sin(phi) * d[:, 2])
    rng = np.sqrt(east ** 2 + north ** 2 + up ** 2)
    alt = np.degrees(np.arcsin(np.clip(up / rng, -1, 1)))
    az = np.degrees(np.arctan2(east, north)) % 360.0
    return alt, az, rng


def _subpoint(p: np.ndarray):
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    q = math.hypot(x, y)
    lat = math.atan2(z, q * (1 - _E2))
    for _ in range(4):
        n = _A / math.sqrt(1 - _E2 * math.sin(lat) ** 2)
        h = q / math.cos(lat) - n
        lat = math.atan2(z, q * (1 - _E2 * n / (n + h)))
    return math.degrees(lat), math.degrees(math.atan2(y, x))


def _sun_teme(jd: np.ndarray) -> np.ndarray:
    n = jd - 2451545.0
    L = np.radians((280.460 + 0.9856474 * n) % 360)
    g = np.radians((357.528 + 0.9856003 * n) % 360)
    lam = L + np.radians(1.915) * np.sin(g) + np.radians(0.020) * np.sin(2 * g)
    eps = np.radians(23.439 - 0.0000004 * n)
    r = (1.00014 - 0.01671 * np.cos(g) - 0.00014 * np.cos(2 * g)) * 149597870.7
    return np.stack([r * np.cos(lam), r * np.cos(eps) * np.sin(lam), r * np.sin(eps) * np.sin(lam)], axis=1)


def _jd_fr(when: datetime):
    from sgp4.api import jday
    return jday(when.year, when.month, when.day, when.hour, when.minute, when.second + when.microsecond * 1e-6)


def _propagate(sat, times: List[datetime]):
    """Return (ok, r_teme, v_teme, jd) for a list of datetimes."""
    jds, frs = [], []
    for t in times:
        j, f = _jd_fr(t)
        jds.append(j)
        frs.append(f)
    jd = np.array(jds)
    fr = np.array(frs)
    e, r, v = sat.sgp4_array(jd, fr)
    return (np.asarray(e) == 0), np.asarray(r), np.asarray(v), jd + fr


def find_tle(name: str) -> Optional[Dict[str, str]]:
    from app.services import satellite_service as ss
    tles = ss.fetch_tle_data() or []
    nm = name.upper().strip()
    if nm == "ISS":
        for t in tles:
            if t["name"].upper().startswith("ISS (ZARYA)"):
                return t
        for t in tles:
            if t["name"].upper().startswith("ISS"):
                return t
        return None
    for t in tles:
        if t["name"].upper() == nm:
            return t
    for t in tles:
        if nm in t["name"].upper():
            return t
    return None


def _compass(az: float) -> str:
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return names[int((az + 11.25) // 22.5) % 16]


def compute_passes(sat, lat: float, lon: float, start: datetime, hours: float = 36.0, step_s: int = 20,
                   limit: int = 6, alt_m: float = 0.0) -> List[Dict[str, Any]]:
    n = int(hours * 3600 / step_s)
    times = [start + timedelta(seconds=step_s * k) for k in range(n)]
    ok, r, _, jd = _propagate(sat, times)
    theta = _gmst_rad(jd)
    c, s = np.cos(theta), np.sin(theta)
    ecef = np.stack([r[:, 0] * c + r[:, 1] * s, -r[:, 0] * s + r[:, 1] * c, r[:, 2]], axis=1)
    alt, az, _ = _altaz(ecef - _obs_ecef(lat, lon, alt_m), lat, lon)
    alt = np.where(ok, alt, -90.0)
    # sunlit satellite? (cylindrical Earth shadow)
    sun = _sun_teme(jd)
    sh = sun / np.linalg.norm(sun, axis=1)[:, None]
    dot = np.sum(r * sh, axis=1)
    perp = np.sqrt(np.maximum(np.sum(r * r, axis=1) - dot ** 2, 0))
    sunlit = ~((dot < 0) & (perp < _A))
    # observer darkness: sun altitude below -6 degrees
    sun_ecef = _teme_to_ecef(sun, theta)
    sun_alt, _, _ = _altaz(sun_ecef - _obs_ecef(lat, lon, alt_m), lat, lon)
    dark = sun_alt < -6.0

    above = alt > 0
    passes: List[Dict[str, Any]] = []
    i = 0
    while i < n and len(passes) < limit:
        if not above[i]:
            i += 1
            continue
        j = i
        while j < n and above[j]:
            j += 1
        seg = slice(i, j)
        k = i + int(np.argmax(alt[seg]))
        vis = bool(np.any(sunlit[seg] & dark[seg] & (alt[seg] > 10.0)))
        t_rise = times[i]
        t_set = times[j - 1]
        passes.append({
            "rise_epoch": int(t_rise.timestamp()), "rise_az": round(float(az[i]), 0), "rise_dir": _compass(az[i]),
            "max_epoch": int(times[k].timestamp()), "max_alt": round(float(alt[k]), 0),
            "max_az": round(float(az[k]), 0), "max_dir": _compass(az[k]),
            "set_epoch": int(t_set.timestamp()), "set_az": round(float(az[j - 1]), 0), "set_dir": _compass(az[j - 1]),
            "duration_s": int((j - i) * step_s), "in_progress": bool(i == 0),
            "visible": vis,
        })
        i = j
    return passes


def _orbit_type(alt_km: float) -> str:
    if alt_km < 2000:
        return "Low Earth orbit (LEO)"
    if 34000 < alt_km < 37000:
        return "Geostationary / geosynchronous orbit"
    if alt_km < 34000:
        return "Medium Earth orbit (MEO)"
    return "High or elliptical orbit"


def satellite_info(name: str, lat: float, lon: float, when: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    from sgp4.api import Satrec
    tle = find_tle(name)
    if tle is None:
        return None
    when = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sat = Satrec.twoline2rv(tle["tle1"], tle["tle2"])
    ok, r, v, jd = _propagate(sat, [when])
    if not ok[0]:
        return None
    theta = _gmst_rad(jd)
    ecef = _teme_to_ecef(r, theta)
    sub_lat, sub_lon = _subpoint(ecef[0])
    rad = float(np.linalg.norm(ecef[0]))
    alt_km = rad - _A * (1 - 0.00335281 * math.sin(math.radians(sub_lat)) ** 2)
    speed = float(np.linalg.norm(v[0]))
    al, az, rng = _altaz(ecef - _obs_ecef(lat, lon, 0.0), lat, lon)
    sun = _sun_teme(jd)
    sh = sun / np.linalg.norm(sun, axis=1)[:, None]
    dot = float(np.sum(r[0] * sh[0]))
    perp = math.sqrt(max(float(np.sum(r[0] ** 2)) - dot ** 2, 0))
    sunlit = not (dot < 0 and perp < _A)

    n_rad_s = sat.no_kozai / 60.0
    a = (_MU / n_rad_s ** 2) ** (1 / 3)
    ecc = float(sat.ecco)
    perigee = a * (1 - ecc) - _A
    apogee = a * (1 + ecc) - _A
    period_min = 2 * math.pi / sat.no_kozai
    incl = math.degrees(sat.inclo)
    ds = str(sat.intldesg).strip()
    intl = ""
    launch_year = ""
    if len(ds) >= 5 and ds[:2].isdigit():
        yy = int(ds[:2])
        y = 1900 + yy if yy >= 57 else 2000 + yy
        intl = f"{y}-{ds[2:5]}{ds[5:]}"
        launch_year = str(y)
    epoch_jd = sat.jdsatepoch + sat.jdsatepochF
    age_days = float(jd[0] - epoch_jd)

    is_iss = name.upper().strip() == "ISS" or tle["name"].upper().startswith("ISS (ZARYA)")
    ident = [["Name", tle["name"]], ["NORAD catalogue number", str(sat.satnum)]]
    if intl:
        ident.append(["International designator", intl])
    if launch_year:
        ident.append(["Launch year", launch_year])
    ident.append(["Orbit type", _orbit_type(alt_km)])
    up = "above your horizon" if al[0] > 0 else "below your horizon"
    live = [
        ["Altitude", f"{alt_km:,.0f} km above the surface"],
        ["Speed", f"{speed:.2f} km/s ({speed * 3600:,.0f} km/h)"],
        ["Over", f"{abs(sub_lat):.2f}°{'N' if sub_lat >= 0 else 'S'}, {abs(sub_lon):.2f}°{'E' if sub_lon >= 0 else 'W'}"],
        ["From you", f"{rng[0]:,.0f} km away, {al[0]:.0f}° high toward {_compass(az[0])} ({up})"],
        ["Lighting", "in sunlight" if sunlit else "in Earth's shadow"],
    ]
    orbit = [
        ["Orbital period", f"{period_min:.1f} minutes ({1440 / period_min:.2f} orbits a day)"],
        ["Inclination", f"{incl:.2f}°"],
        ["Eccentricity", f"{ecc:.5f}"],
        ["Lowest point", f"{perigee:,.0f} km"],
        ["Highest point", f"{apogee:,.0f} km"],
        ["Orbit data age", f"{age_days:.1f} days"],
    ]
    secs = [{"title": "Identity", "rows": ident}, {"title": "Live", "rows": live}, {"title": "Orbit", "rows": orbit}]
    about = ""
    if is_iss:
        secs.append({"title": "About the station", "rows": ISS_FACTS})
        about = "The International Space Station is the largest object humans have ever put in space."
    elif "STARLINK" in tle["name"].upper():
        about = "A SpaceX Starlink internet satellite. Thousands orbit together in shells; fresh launches appear as a bright 'train'."
    passes = compute_passes(sat, lat, lon, when)
    return {"kind": "satellite", "iss": is_iss, "name": tle["name"], "about": about, "sections": secs,
            "passes": passes, "time": when.isoformat()}
