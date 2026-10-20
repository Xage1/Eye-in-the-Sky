"""
app/services/astronomy_service.py

Sun / Moon conditions for a location, computed locally with astropy.
No external API and no key. Replaces the old ipgeolocation.io wrapper,
which needed an ASTRONOMY_API_KEY this project never had.
"""

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, get_body, get_sun
from astropy.time import Time
from astropy.utils import iers

try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "ignore"
except Exception:
    pass


def _twilight(sun_alt: float) -> str:
    if sun_alt > 0:
        return "day"
    if sun_alt > -6:
        return "civil_twilight"
    if sun_alt > -12:
        return "nautical_twilight"
    if sun_alt > -18:
        return "astronomical_twilight"
    return "night"


def get_astronomy_data(lat: float, lon: float, date: str = None) -> dict:
    """`date` is an optional ISO string (e.g. '2026-12-14' or '2026-12-14T21:00:00', UTC)."""
    try:
        t = Time(date) if date else Time.now()
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
        frame = AltAz(obstime=t, location=location)

        sun = get_sun(t)
        moon = get_body("moon", t, location)
        sun_alt = float(sun.transform_to(frame).alt.deg)
        moon_alt = float(moon.transform_to(frame).alt.deg)

        elongation = sun.separation(moon)
        phase_angle = np.arctan2(
            sun.distance * np.sin(elongation),
            moon.distance - sun.distance * np.cos(elongation),
        )
        illumination = float((1 + np.cos(phase_angle)) / 2)

        twilight = _twilight(sun_alt)
        return {
            "time_utc": t.utc.iso,
            "sun": {"altitude_deg": round(sun_alt, 2), "twilight": twilight},
            "moon": {
                "altitude_deg": round(moon_alt, 2),
                "above_horizon": moon_alt > 0,
                "illumination_pct": round(illumination * 100, 1),
            },
            "is_dark": twilight == "night",
        }
    except Exception as exc:
        return {"error": f"astronomy calculation failed: {exc}"}