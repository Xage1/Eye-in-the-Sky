from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.models.star_watchlist import StarWatchlist
from app.schemas.star_watchlist import StarWatchCreate, StarWatchOut
from app.utils.deps import get_current_user, get_db
from app.utils.constellations import load_constellations
from app.models.user import User

router = APIRouter(prefix="/watchlist", tags=["StarWatchlist"])

VALID_CONSTELLATIONS = load_constellations()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: StarWatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Prevent Duplicates
    stmt = select(StarWatchlist).where(
        StarWatchlist.user_id == current_user.id,
        StarWatchlist.star_name == payload.star_name,
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=400, detail= "Star already in Watchlist")
    
    entry = StarWatchlist(
        user_id=current_user.id,
        star_name=payload.star_name,
        description=payload.description,
    )

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return {
        "id": entry.id,
        "star_name": entry.star_name,
        "description": entry.description
    }

@router.get("/", response_model=list[StarWatchOut])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(StarWatchlist)
        .where(StarWatchlist.user_id == current_user.id)
    )
    return result.scalars().all()