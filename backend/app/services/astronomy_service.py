"""
app/services/astronomy_service.py

Wrapper around the ipgeolocation astronomy API.

"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ASTRONOMY_API_KEY")
BASE_URL = "https://api.ipgeolocation.io/v2/astronomy"


def get_astronomy_data(lat: float, lon: float, date: str = None) -> dict:
    if not API_KEY:
        return {"error": "ASTRONOMY_API_KEY not configured"}

    params = {"apiKey": API_KEY, "lat": lat, "long": lon}
    if date:
        params["date"] = date

    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        return {"error": f"Astronomy API {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"error": str(exc)}