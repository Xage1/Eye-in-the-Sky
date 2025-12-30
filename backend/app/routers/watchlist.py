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


@router.post("/", response_model=StarWatchCreate, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: StarWatchCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.constellation not in VALID_CONSTELLATIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid constellation name"
        )

    existing = (
        db.query(StarWatchlist)
        .filter_by(user_id=user.id, constellation=payload.constellation)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Constellation already in watchlist"
        )

    item = StarWatchlist(
        user_id=user.id,
        constellation=payload.constellation
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


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