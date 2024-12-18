import requests

def get_coordinates(city):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={city}"
    response = requests.get(url)
    return response.json()