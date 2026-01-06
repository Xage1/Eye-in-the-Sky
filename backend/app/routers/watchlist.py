from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.star_watchlist import StarWatchlist
from app.schemas.star_watchlist import StarWatchCreate, StarWatchOut
from app.utils.deps import get_current_user, get_db
from app.utils.constellations import load_constellations
from app.utils.stars import load_star_map
from app.models.user import User

router = APIRouter(prefix="/watchlist", tags=["StarWatchlist"])

VALID_CONSTELLATIONS = load_constellations()
STAR_MAP = load_star_map()  # dict[str, dict]


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=StarWatchOut,
)
async def add_to_watchlist(
    payload: StarWatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 🔹 Normalize once
    normalized_star = payload.star_name.strip().lower()

    star_data = STAR_MAP.get(normalized_star)
    if not star_data:
        raise HTTPException(
            status_code=400,
            detail="Star not found in catalog",
        )

    constellation = star_data["constellation"]

    if constellation not in VALID_CONSTELLATIONS:
        raise HTTPException(
            status_code=500,
            detail="Resolved constellation is invalid (catalog integrity error)",
        )

    # 🚫 Prevent duplicates per user
    stmt = select(StarWatchlist).where(
        StarWatchlist.user_id == current_user.id,
        StarWatchlist.star_name == star_data["proper_name"],
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Star already in watchlist",
        )

    entry = StarWatchlist(
        user_id=current_user.id,
        star_name=star_data["proper_name"],
        constellation=constellation,
        description=payload.description,
    )

    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return entry


@router.get("/", response_model=list[StarWatchOut])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(StarWatchlist)
        .where(StarWatchlist.user_id == current_user.id)
        .order_by(StarWatchlist.added_at.desc())
    )
    return result.scalars().all()