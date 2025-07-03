
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.astronomyapi.com/api/v2"
API_KEY = os.getenv("ASTRONOMY_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:
    raise EnvironmentError("ASTRONOMY_API_KEY not found in .env")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


async def get_constellation_data(lat: float, lon: float, date: str = None):
    try:
        if date:
            url = f"{API_BASE}/bodies/positions?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}"
        else:
            url = f"{API_BASE}/constellations?latitude={lat}&longitude={lon}"

        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS)
            res.raise_for_status()
            return res.json()

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


async def get_events(lat: float, lon: float):
    try:
        url = f"{API_BASE}/events?latitude={lat}&longitude={lon}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS)
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


async def get_star_rise_set(lat: float, lon: float, date: str):
    try:
        url = f"{API_BASE}/bodies/rise-set?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}&bodies=stars"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS)
            res.raise_for_status()
            return res.json()
    except Exception as e:
        return {"error": str(e)}


async def get_moon_phase(lat: float, lon: float, date: str):
    try:
        url = f"{API_BASE}/moon-phases?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS)
            res.raise_for_status()
            return res.json()
    except Exception as e:
        return {"error": str(e)}


async def get_visibility_forecast(lat: float, lon: float):
    try:
        if not OPENWEATHER_API_KEY:
            raise EnvironmentError("OPENWEATHER_API_KEY not found in .env")

        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()
            visibility_km = data.get("visibility", 0) / 1000  # meters to km
            cloudiness = data.get("clouds", {}).get("all", 0)
            return {
                "visibility_km": visibility_km,
                "cloud_coverage_percent": cloudiness,
                "sky_clear": cloudiness < 25
            }
    except Exception as e:
        return {"error": str(e)}