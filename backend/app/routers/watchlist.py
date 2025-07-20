from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.star_watchlist import StarWatchlist
from app.schemas.star_watchlist import StarWatchCreate, StarWatchOut
from app.database import SessionLocal
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

def get_db(): ...

@router.post("/", response_model=StarWatchOut)
async def add_star(
    item: StarWatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    star = StarWatchlist(**item.dict(), user_id=current_user.id)
    db.add(star)
    await db.commit()
    await db.refresh(star)
    return star

@router.get("/", response_model=list[StarWatchOut])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(StarWatchlist).where(StarWatchlist.user_id == current_user.id)
    )
    return result.scalars().all()