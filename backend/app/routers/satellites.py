from fastapi import APIRouter
from app.utils.tle import fetch_and_parse_tle
from app.utils.notify import get_iss_position

router = APIRouter(prefix="/satellites", tags=["Satellites"])

@router.get("/tle")
async def get_satellite_tle():
    return await fetch_and_parse_tle()

@router.get("/iss")
async def get_iss():
    return await get_iss_position()