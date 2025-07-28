import requests
from datetime import datetime
from sgp4.api import Satrec, WGS72
from math import degrees, atan2, sqrt, acos
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, ITRS, CartesianRepresentation
import astropy.units as u



TLE_URL = "https://celestrak.com/NORAD/elements/active.txt"

def fetch_tle_data():
    response = requests.get(TLE_URL)
    lines = response.text.strip().splitlines()
    satellites = []

    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        try:
            satrec= Satrec.twoline2rv(tle1, tle2)
            satellites.append({
                "name": name,
                "satrec": satrec
            })
        except Exception:
            continue
    return satellites

def is_satellite_visible(satrec, observer, time_utc):
    """
    Check if a satellite is visible from the observer's location at a given UTC time.
    """

    error_code, postion, _ = satrec.sgp4(time_utc.year, time_utc.timetuple().tm_yday, time_utc.hour / 24.0)
    if error_code != 0:
        return None
    

    # Convert ECI position to AltAz coordinates
    sat_cartesian = CartesianRepresentation(*[coord * 1000 for coord in postion], unit=u.m)
    itrs = ITRS(sat_cartesian, obstime=Time(time_utc))
    altaz = itrs.transform_to(AltAz(obstime=Time(time_utc), location=observer))


    if altaz.alt > 0 * u.deg:
        return {
            "azimuth": round(altaz.az.deg, 2),
            "elevation": round(altaz.alt.deg, 2)
        }
    
    return None

def get_visible_satellites(lat, lon, alt_m=0, when=None, max_results=10):
    """
    Get a list of visible satellites from the observer's location at a given UTC time.
    """

    time_utc = when or datetime.utcnow()
    observer = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=alt_m * u.m)
    tle_data = fetch_tle_data()

    visible = []

    for sat in tle_data:
        visibility = is_satellite_visible(sat["satrec"], observer, time_utc)
        if visibility:
            visible.append({
                "name": sat["name"],
                "azimuth": visibility["azimuth"],
                "elevation": visibility["elevation"]
            })
            if len(visible) >= max_results:
                break

    return visible