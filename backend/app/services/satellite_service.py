import httpx
import os

N2YO_API_KEY = os.getenv("N2YO_API_KEY")

async def get_visible_satellites(lat: float, lon: float, alt: float = 0):
    if not N2YO_API_KEY:
        raise EnvironmentError("N2YO_API_KEY not set")

    url = f"https://api.n2yo.com/rest/v1/satellite/visualpasses/25544/{lat}/{lon}/{alt}/1/30/&apiKey={N2YO_API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()