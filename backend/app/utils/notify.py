import httpx

async def get_iss_position():
    async with httpx.AsyncClient() as client:
        res = await client.get("http://api.open-notify.org/iss-now.json")
        return res.json()
