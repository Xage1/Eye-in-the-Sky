import json
from pathlib import Path
from datetime import datetime
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u

# === Load star and constellation data ===
def load_data():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    stars_path = data_dir / "stars.json"
    constellations_path = data_dir / "constellations.json"

    with stars_path.open("r", encoding="utf-8") as f:
        stars = json.load(f)
    with constellations_path.open("r", encoding="utf-8") as f:
        constellations = json.load(f)

    return stars, constellations


# === Visible Constellations ===
def identify_visible_constellations(lat, lon, azimuth, when=None, radius=10):
    stars, constellations = load_data()
    when = when or datetime.utcnow()
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    time = Time(when)
    altaz_frame = AltAz(obstime=time, location=location)
    center_coord = SkyCoord(az=azimuth * u.deg, alt=45 * u.deg, frame=altaz_frame)

    closest_constellation = None
    min_dist = 999
    for const_name, const_data in constellations.items():
        try:
            major_stars = const_data.get("major_stars", [])
            if not major_stars:
                continue
            star_coords = []
            for s in major_stars:
                try:
                    match = next((x for x in stars if x.get("name") == s), None)
                    if match:
                        star_coords.append(SkyCoord(ra=match["ra"] * u.deg, dec=match["dec"] * u.deg))
                except Exception:
                    continue
            if not star_coords:
                continue
            avg_ra = sum(sc.ra.deg for sc in star_coords) / len(star_coords)
            avg_dec = sum(sc.dec.deg for sc in star_coords) / len(star_coords)
            const_coord = SkyCoord(ra=avg_ra * u.deg, dec=avg_dec * u.deg)
            const_altaz = const_coord.transform_to(altaz_frame)
            if const_altaz.alt < 0 * u.deg:
                continue
            dist = center_coord.separation(const_altaz).deg
            if dist < min_dist:
                min_dist = dist
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
        except Exception:
            continue
    return closest_constellation


# === Nearby Stars (Simplified version) ===
def find_nearby_stars(lat, lon, azimuth, radius=15, when=None):
    stars, _ = load_data()
    when = when or datetime.utcnow()
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    time = Time(when)
    altaz_frame = AltAz(obstime=time, location=location)
    center_coord = SkyCoord(az=azimuth * u.deg, alt=45 * u.deg, frame=altaz_frame)

    visible = []
    for s in stars:
        try:
            star_coord = SkyCoord(ra=s["ra"] * u.deg, dec=s["dec"] * u.deg, frame="icrs")
            star_altaz = star_coord.transform_to(altaz_frame)
            if star_altaz.alt <= 0 * u.deg:
                continue
            separation = center_coord.separation(star_altaz).deg
            if separation <= radius:
                visible.append({
                    "name": s.get("name"),
                    "mag": s.get("mag"),
                    "constellation": s.get("constellation"),
                    "distance_deg": round(separation, 2),
                })
        except Exception:
            continue
    return sorted(visible, key=lambda s: s.get("mag", 99))