from fastapi import APIRouter 

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/profile")
async def get_profile():
    return {"user": "Profile details"}