from fastapi import APIRouter
import requests

router = APIRouter(prefix="/constellations", tags=["Constellations"])

@router.get("/")
async def get_constellations(lat: float, lon: float):
    url= f"https://api.astronomyapi.com/constellations?lat={lat}&lon={lon}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()