"""
Dependency injection for Eye in the Sky.
Includes auth, DB session, and premium feature gating.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.subscription import UserSubscription, PlanTier, SubscriptionStatus
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ── Database session ───────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with SessionLocal() as db:
        yield db


# ── Current user ───────────────────────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    payload = decode_access_token(token)
    if payload is None or not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == int(sub)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


# ── Active subscription helper ─────────────────────────────────────────────────
async def _get_active_plan(user: User, db: AsyncSession) -> PlanTier:
    """Return the user's current active plan tier."""
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user.id)
    )
    sub = result.scalars().first()
    if sub and sub.status == SubscriptionStatus.active:
        return sub.plan
    return PlanTier.free


# ── Role guards ────────────────────────────────────────────────────────────────
async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Only admin role can access this route."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ── Plan guards ────────────────────────────────────────────────────────────────
async def require_pro(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Requires Pro or Premium subscription. Free users are rejected."""
    if current_user.role == UserRole.admin:
        return current_user
    plan = await _get_active_plan(current_user, db)
    if plan not in (PlanTier.pro, PlanTier.premium):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Pro or Premium subscription required. Upgrade at /payments/plans",
        )
    return current_user


async def require_premium(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Requires Premium subscription only."""
    if current_user.role == UserRole.admin:
        return current_user
    plan = await _get_active_plan(current_user, db)
    if plan != PlanTier.premium:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Premium subscription required. Upgrade at /payments/plans",
        )
    return current_user


def require_self_or_admin(user_id: int):
    """
    Factory dependency — user can only access their own resource,
    unless they are admin.

    Usage:
      @router.get("/{user_id}")
      async def get_user(
          user_id: int,
          current_user: User = Depends(require_self_or_admin(user_id))
      ):
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.admin:
            return current_user
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own resources",
            )
        return current_user
    return _check