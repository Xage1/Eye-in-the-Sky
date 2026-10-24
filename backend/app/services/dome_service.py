"""
Whole-sky payload for on-device rendering.

Stars are static, so they go out once as RA/Dec of date and the phone works out Alt/Az itself from the
clock and GPS. Moving bodies (Sun, Moon, planets, satellites, ISS) go out as Alt/Az and are refreshed
every few seconds.
"""
import logging

import numpy as np

from app.services import scene_fast as sf

logger = logging.getLogger(__name__)


def _stars_payload(mag_limit: float, when):
    cat = sf._load_catalogue()
    if cat is None:
        return [], {}
    ra, dec = sf._stars_of_date(cat, when)
    idx = np.flatnonzero(cat["mag"] <= mag_limit)
    idx = idx[np.argsort(cat["mag"][idx])]
    rows, names = [], {}
    for i in idx:
        hr = int(cat["hr"][i])
        m = float(cat["mag"][i])
        rows.append([hr, round(m, 2), round(float(ra[i]), 4), round(float(dec[i]), 4)])
        nm = cat["name"][i] or ""
        if str(nm).startswith("HR "):
            nm = ""
        con = cat["constellation"][i] or ""
        if nm or m <= 4.0:
            names[str(hr)] = [str(nm), str(con)]
    return rows, names


async def build_dome(lat: float, lon: float, when, mag_limit: float = 5.5, include_stars: bool = True) -> dict:
    when = sf._utc(when)
    out = {
        "time": when.isoformat(),
        "gmst_deg": round(float(sf._gmst_deg(sf._jd(when))), 4),
        "observer": {"lat": lat, "lon": lon},
    }
    if include_stars:
        rows, names = _stars_payload(mag_limit, when)
        out["stars"] = rows
        out["names"] = names

    try:
        planets = sf.get_planet_positions(lat, lon, when, 0.0, 90.0, 0.0, 1000, 1000, 180.0, 180.0)
        out["planets"] = [{"name": p["name"], "az": p["azimuth_deg"], "alt": p["altitude_deg"]} for p in planets]
    except Exception as exc:
        logger.warning("dome planets failed: %s", exc)
        out["planets"] = []

    try:
        sats = sf.get_visible_satellites(lat, lon, 0.0, when, 40)
        out["satellites"] = [{"name": s["name"], "az": s["azimuth_deg"], "alt": s["altitude_deg"]} for s in sats]
    except Exception as exc:
        logger.warning("dome satellites failed: %s", exc)
        out["satellites"] = []

    try:
        iss = await sf.get_iss_position(lat, lon, when)
        out["iss"] = {
            "available": bool(iss.get("available")),
            "az": iss.get("azimuth_deg"),
            "alt": iss.get("altitude_deg"),
        }
    except Exception as exc:
        logger.warning("dome iss failed: %s", exc)
        out["iss"] = {"available": False}
    return out
