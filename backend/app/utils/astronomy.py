"""
app/utils/astronomy.py

Astronomy utility functions — wrappers around AstronomyAPI and OpenWeather.
API keys are checked at request time, not import time, so the app boots
cleanly even when keys are not yet configured.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.astronomyapi.com/api/v2"


def _get_api_key() -> str | None:
    return os.getenv("ASTRONOMY_API_KEY")


def _get_weather_key() -> str | None:
    return os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY")


def _headers() -> dict:
    key = _get_api_key()
    return {"Authorization": f"Bearer {key}"} if key else {}


async def get_constellation_data(lat: float, lon: float, date: str = None):
    if not _get_api_key():
        return {"error": "ASTRONOMY_API_KEY not configured"}
    try:
        if date:
            url = f"{API_BASE}/bodies/positions?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}"
        else:
            url = f"{API_BASE}/constellations?latitude={lat}&longitude={lon}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=_headers())
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


async def get_events(lat: float, lon: float):
    if not _get_api_key():
        return {"error": "ASTRONOMY_API_KEY not configured"}
    try:
        url = f"{API_BASE}/events?latitude={lat}&longitude={lon}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=_headers())
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


async def get_star_rise_set(lat: float, lon: float, date: str):
    if not _get_api_key():
        return {"error": "ASTRONOMY_API_KEY not configured"}
    try:
        url = f"{API_BASE}/bodies/rise-set?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}&bodies=stars"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=_headers())
            res.raise_for_status()
            return res.json()
    except Exception as e:
        return {"error": str(e)}


async def get_moon_phase(lat: float, lon: float, date: str):
    if not _get_api_key():
        return {"error": "ASTRONOMY_API_KEY not configured"}
    try:
        url = f"{API_BASE}/moon-phases?latitude={lat}&longitude={lon}&from_date={date}&to_date={date}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=_headers())
            res.raise_for_status()
            return res.json()
    except Exception as e:
        return {"error": str(e)}


async def get_visibility_forecast(lat: float, lon: float):
    key = _get_weather_key()
    if not key:
        return {"error": "WEATHER_API_KEY not configured"}
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&units=metric"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()
            visibility_km = data.get("visibility", 0) / 1000
            cloudiness = data.get("clouds", {}).get("all", 0)
            return {
                "visibility_km": visibility_km,
                "cloud_coverage_percent": cloudiness,
                "sky_clear": cloudiness < 25,
            }
    except Exception as e:
        return {"error": str(e)}