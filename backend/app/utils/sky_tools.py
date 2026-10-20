import json
import re
from functools import lru_cache
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_constellation
from astropy.time import Time
from astropy.utils import iers

try:
    # Never block on a download or fail when IERS tables lack current dates.
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "ignore"
except Exception:
    pass

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_RA = re.compile(r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$")
_DEC = re.compile(r"^[+-]?\d{1,2}:\d{2}:\d{2}(\.\d+)?$")


@lru_cache(maxsize=1)
def _constellations():
    with (DATA_DIR / "constellations.json").open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _catalogue():
    """Parse the Harvard Revised catalogue once: (SkyCoord array, HR numbers, magnitudes)."""
    with (DATA_DIR / "stars.json").open("r", encoding="utf-8") as f:
        raw = json.load(f)

    ra, dec, hr, mag = [], [], [], []
    for row in raw:
        r = str(row.get("RA", "")).strip()
        d = str(row.get("DEC", "")).strip()
        if not (_RA.match(r) and _DEC.match(d)):
            continue
        try:
            m = float(row["MAG"])
            n = int(row["harvard_ref_#"])
        except (KeyError, TypeError, ValueError):
            continue
        ra.append(r)
        dec.append(d)
        hr.append(n)
        mag.append(m)

    coords = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg), frame="icrs")
    return coords, np.array(hr), np.array(mag)


def _frame_and_center(lat, lon, azimuth, altitude, when):
    time = Time(when) if when else Time.now()
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    frame = AltAz(obstime=time, location=location)
    center = SkyCoord(az=azimuth * u.deg, alt=altitude * u.deg, frame=frame)
    return frame, center


def identify_visible_constellations(lat, lon, azimuth=0.0, altitude=45.0, when=None):
    """Constellation the user is looking at (IAU boundaries via astropy)."""
    _, center = _frame_and_center(lat, lon, azimuth, altitude, when)
    name = str(get_constellation(center.icrs))
    info = _constellations().get(name, {})
    return {
        "name": name,
        "description": info.get("description"),
        "myth": info.get("myth"),
        "discoverer": info.get("discoverer"),
        "year": info.get("year"),
        "brightest_star": info.get("brightest_star"),
        "major_stars": info.get("major_stars"),
    }


def find_nearby_stars(lat, lon, azimuth=0.0, altitude=45.0, radius=15.0, when=None, limit=50):
    """Brightest catalogue stars above the horizon within `radius` degrees of the viewing direction."""
    coords, hr, mag = _catalogue()
    frame, center = _frame_and_center(lat, lon, azimuth, altitude, when)

    altaz = coords.transform_to(frame)
    sep = center.separation(altaz).deg
    idx = np.flatnonzero((altaz.alt.deg > 0) & (sep <= radius))
    if idx.size == 0:
        return []

    idx = idx[np.argsort(mag[idx])][:limit]
    consts = get_constellation(coords[idx])

    return [
        {
            "hr": int(hr[i]),
            "mag": float(mag[i]),
            "constellation": str(consts[k]),
            "altitude_deg": round(float(altaz.alt.deg[i]), 2),
            "azimuth_deg": round(float(altaz.az.deg[i]), 2),
            "distance_deg": round(float(sep[i]), 2),
        }
        for k, i in enumerate(idx)
    ]

def warm_up() -> None:
    """Pay the one-off catalogue parse and astropy start-up cost at boot, not on the first request."""
    try:
        find_nearby_stars(0.0, 0.0, 0.0, 45.0, 1.0)
        identify_visible_constellations(0.0, 0.0, 0.0, 45.0)
    except Exception:
        pass


warm_up()