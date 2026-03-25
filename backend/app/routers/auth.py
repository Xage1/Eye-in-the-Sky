"""
Authentication router — hardened for Eye in the Sky.

Features:
  - Admin whitelist — only specific emails can register as admin
  - Role assignment on signup
  - Refresh token flow (Redis-backed, revocable)
  - Full user profile endpoint
  - Profile update endpoint
  - Password change
  - Account deactivation
"""

import os
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.user_settings import UserSettings
from app.models.subscription import UserSubscription, PlanTier, SubscriptionStatus
from app.schemas.user import UserOut, UserAdminOut, UserCreate, UserProfileUpdate
from app.utils.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
)
from app.utils.deps import get_db, get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Admin whitelist — set in .env as comma-separated emails ───────────────────
_ADMIN_EMAILS = set(
    e.strip().lower()
    for e in os.getenv("ADMIN_EMAILS", "").split(",")
    if e.strip()
)

# ── Schemas (inline to keep router self-contained) ────────────────────────────
from pydantic import BaseModel, EmailStr
from typing import Optional


class SignupIn(BaseModel):
    name:     str
    email:    EmailStr
    password: str


class LoginIn(BaseModel):
    email:    EmailStr
    password: str


class TokenOut(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    role:          UserRole
    plan:          str = "free"


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password:     str


class DeactivateIn(BaseModel):
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _assign_role(email: str) -> UserRole:
    """Admin if email is in the whitelist, otherwise regular user."""
    if email.lower() in _ADMIN_EMAILS:
        return UserRole.admin
    return UserRole.user


async def _get_user_plan(user_id: int, db: AsyncSession) -> str:
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    sub = result.scalars().first()
    if sub and sub.status == SubscriptionStatus.active:
        return sub.plan.value
    return "free"


# ── Signup ────────────────────────────────────────────────────────────────────
@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupIn, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. Role is determined automatically:
    - Emails in ADMIN_EMAILS env var → admin
    - All others → user (free plan)
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role = _assign_role(payload.email)

    new_user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=role,
        is_active=True,
        is_verified=False,
        last_login=datetime.now(timezone.utc),
    )
    new_user.settings     = UserSettings()
    new_user.subscription = UserSubscription(
        plan=PlanTier.free,
        status=SubscriptionStatus.active,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token(subject=str(new_user.id))
    logger.info("New user registered | id=%s email=%s role=%s", new_user.id, new_user.email, role)

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         role,
        "plan":         "free",
    }


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    plan = await _get_user_plan(user.id, db)
    token = create_access_token(subject=str(user.id))

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user.role,
        "plan":         plan,
    }


# ── Current user profile ──────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """Full profile for the currently authenticated user."""
    return current_user


# ── Update profile ────────────────────────────────────────────────────────────
@router.patch("/me", response_model=UserOut)
async def update_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's profile fields."""
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ── Change password ───────────────────────────────────────────────────────────
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: PasswordChangeIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}


# ── Deactivate account ────────────────────────────────────────────────────────
@router.post("/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_account(
    payload: DeactivateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    current_user.is_active = False
    await db.commit()
    return {"message": "Account deactivated"}


# ── Admin: list all users ─────────────────────────────────────────────────────
@router.get("/admin/users", response_model=list[UserAdminOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — list all registered users."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


# ── Admin: set user role ──────────────────────────────────────────────────────
@router.patch("/admin/users/{user_id}/role")
async def set_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — change a user's role."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    await db.commit()
    return {"message": f"User {user_id} role updated to {role}"}


# ── Auth health check ─────────────────────────────────────────────────────────
@router.get("/health")
async def auth_health(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {
        "status":      "ok",
        "total_users": len(users),
        "admins":      sum(1 for u in users if u.role == UserRole.admin),
        "active":      sum(1 for u in users if u.is_active),
    }