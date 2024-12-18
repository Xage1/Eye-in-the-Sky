import requests

def fetch_constellation_data(lat, lon):
    url = f"https://api.astronomyapi.com/constellations?lat={lat}&lon={lon}"
    response = requests.get(url)
    return response.json()