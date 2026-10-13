import httpx


async def reverse_geocode(lat: float, lon: float):
    """
    Resolve a (city, country) pair for a lat/lon via OpenStreetMap
    Nominatim. Returns ("Unknown", "Unknown") on any failure -- this
    is best-effort labeling, never a hard dependency.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "EyeInTheSky/1.0 (astronomy app)"}
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            data = res.json()
            address = data.get("address", {})
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or "Unknown"
            )
            country = address.get("country", "Unknown")
            return city, country
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return "Unknown", "Unknown"
