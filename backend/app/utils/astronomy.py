import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.astronomyapi.com/api/v2"
API_KEY = os.getenv("ASTRONOMY_API_KEY")

async def get_constellation_data(lat, lon):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE}/bodies/positions?latitude={lat}&longitude={lon}", headers=headers)
        return res.json()

async def get_events(lat, lon):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE}/events?latitude={lat}&longitude={lon}", headers=headers)
        return res.json()