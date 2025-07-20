from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsOut
from app.database import SessionLocal
from app.utils.deps import get_current_user
from app.models.user import User
from sqlalchemy.future import select

router = APIRouter(prefix="/user/settings", tags=["User Settings"])

def get_db(): ...

@router.get("/", response_model=UserSettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@router.patch("/", response_model=UserSettingsOut)
async def update_settings(
    updates: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    settings = result.scalar()
    for k, v in updates.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    await db.commit()
    return settings
