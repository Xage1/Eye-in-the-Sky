import httpx

async def reverse_geocode(lat: float, lon: float):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            data = res.json()
            address = data.get("address", {})
            return address.get("city", "Unknown") or address.get("town", "Unknown") or address.get("village", "Unknown")
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return "Unknown"