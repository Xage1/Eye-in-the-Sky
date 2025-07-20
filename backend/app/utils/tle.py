import httpx

async def fetch_and_parse_tle():
    async with httpx.AsyncClient() as client:
        res = await client.get("https://celestrak.com/NORAD/elements/stations.txt")
        return res.text  # you can parse with sgp4 later