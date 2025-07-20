import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE = "https://api.weatherapi.com/v1"

async def get_visibility_forecast(lat, lon):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{WEATHER_BASE}/forecast.json",
                params={"key": API_KEY, "q": f"{lat},{lon}", "days": 1}
            )
            data = res.json()
            visibility_km = data["forecast"]["forecastday"][0]["day"]["avgvis_km"]
            return {"visibility_km": visibility_km}
    except Exception as e:
        return {"error": str(e)}