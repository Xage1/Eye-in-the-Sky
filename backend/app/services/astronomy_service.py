import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ASTRONOMY_API_KEY")
BASE_URL = "https://api.ipgeolocation.io/v2/astronomy"


def get_astronomy_data(lat: float, lon: float, date: str = None):
    if not API_KEY:
        raise EnvironmentError("ASTRONOMY_API_KEY not found in .env")

    params = {
        "apiKey": API_KEY,
        "lat": lat,
        "long": lon
    }

    if date:
        params["date"] = date

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Astronomy API error: {response.status_code} {response.text}")

    return response.json()