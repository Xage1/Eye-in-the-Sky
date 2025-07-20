import json
from pathlib import Path
from datetime import datetime

from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u


# === Load star and constellation data ===
def load_data():
    with open(Path("app/data/stars.json"), "r", encoding="utf-8") as f:
        stars = json.load(f)

    with open(Path("app/data/constellations.json"), "r", encoding="utf-8") as f:
        constellations = json.load(f)

    return stars, constellations


# === Main AR Vision matching logic ===
def get_visible_objects(lat, lon, azimuth, radius=10, when=None):
    stars, constellations = load_data()
    when = when or datetime.utcnow()

    # Observer location and time

    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    time = Time(when)
    altaz_frame = AltAz(obstime=time, location=location)

    # Observation direction (Center of camera view)
    center_coord = SkyCoord(az=azimuth * u.deg, alt=45 * u.deg, frame=altaz_frame)
    results = []

    for star in stars:
        try:
            star_coord = SkyCoord(ra=star["ra"] * u.deg, dec=star["dec"] * u.deg, frame='icrs')
            star_altaz = star_coord.transform_to(altaz_frame)

            if star_altaz.alt > 0 * u.deg:  # Only consider stars above the horizon
                continue

            separation = center_coord.separation(star_altaz).deg
            if separation <= radius:
                star_info = {
                    "name": star.get("name"),
                    "bayer": star.get("bayer"),
                    "mag": star.get("mag"),
                    "ra": star["ra"],
                    "dec": star["dec"],
                    "spectral_type": star.get("spectral_type"),
                    "constellation": star.get("constellation"),
                    "distance_deg": round(separation, 2),
                }
                results.append(star_info)
        except Exception:
            continue

    # Find constellation closest to the center
    closest_constellation = None
    min_dist= 999
    for const_name, const_data in constellations.items():
        try:
            # Rough RA/Dec = average of major star coordinates
            star_coords = [SkyCoord.from_name(name) for name in const_data.get("major_stars", [])]
            if not star_coords:
                continue
            avg_ra= sum(s.ra.deg for s in star_coords) / len(star_coords)
            avg_dec = sum(s.dec.deg for s in star_coords) / len(star_coords)
            const_coord = SkyCoord(ra=avg_ra * u.deg, dec=avg_dec * u.deg)
            const_altaz = const_coord.transform_to(altaz_frame)
            if const_altaz.alt < 0 * u.deg:
                continue
            dist = center_coord.separation(const_altaz).deg
            if dist < min_dist:
                closest_constellation = {
                    "name": const_name,
                    "description": const_data.get("description"),
                    "myth": const_data.get("myth"),
                    "discoverer": const_data.get("discoverer"),
                    "year": const_data.get("year"),
                    "brightest_star": const_data.get("brightest_star"),
                    "major_stars": const_data.get("major_stars"),
                    "distance_deg": round(dist, 2),
                }
                min_dist = dist
        except Exception:
            continue
        return {
            "timestamp": time.iso,
            "location": {
                "latitude": lat,
                "longitude": lon,
            },
            "azimuth": azimuth,
            "angular_radius": radius,
            "visible_stars": sorted(results, key=lambda s: s["mag"]),
            "focused_constellation": closest_constellation,
        }