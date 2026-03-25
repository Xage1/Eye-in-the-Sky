"""
app/schemas/user.py  — Pydantic V2 compatible (from_attributes replaces orm_mode)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl

from app.models.user import UserRole
from app.models.subscription import PlanTier, SubscriptionStatus


# ── Subscription summary (embedded in UserOut) ────────────────────────────────
class SubscriptionSummary(BaseModel):
    plan:    PlanTier
    status:  SubscriptionStatus
    current_period_end: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Settings summary (embedded in UserOut) ────────────────────────────────────
class UserSettingsOut(BaseModel):
    id:                    int
    dark_mode:             bool
    default_difficulty:    str
    notifications_enabled: bool

    model_config = {"from_attributes": True}


# ── Create ────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name:     str
    email:    EmailStr
    password: str


# ── Update profile ────────────────────────────────────────────────────────────
class UserProfileUpdate(BaseModel):
    name:             Optional[str]   = None
    bio:              Optional[str]   = None
    avatar_url:       Optional[str]   = None
    location:         Optional[str]   = None
    country:          Optional[str]   = None
    timezone:         Optional[str]   = None
    language:         Optional[str]   = None
    occupation:       Optional[str]   = None
    astronomy_level:  Optional[str]   = None
    twitter_handle:   Optional[str]   = None
    instagram_handle: Optional[str]   = None
    website_url:      Optional[str]   = None


# ── Full profile out (used by /auth/me and /users/profile) ───────────────────
class UserOut(BaseModel):
    id:               int
    name:             str
    email:            EmailStr
    role:             UserRole
    is_active:        bool
    is_verified:      bool

    # Profile fields
    avatar_url:       Optional[str]      = None
    bio:              Optional[str]      = None
    location:         Optional[str]      = None
    country:          Optional[str]      = None
    timezone:         Optional[str]      = None
    language:         Optional[str]      = None
    occupation:       Optional[str]      = None
    astronomy_level:  Optional[str]      = None
    twitter_handle:   Optional[str]      = None
    instagram_handle: Optional[str]      = None
    website_url:      Optional[str]      = None

    # Timestamps
    created_at:       Optional[datetime] = None
    last_login:       Optional[datetime] = None

    # Nested
    settings:         Optional[UserSettingsOut]    = None
    subscription:     Optional[SubscriptionSummary] = None

    model_config = {"from_attributes": True}


# ── Admin view (includes more detail) ────────────────────────────────────────
class UserAdminOut(UserOut):
    date_of_birth:    Optional[datetime] = None
    updated_at:       Optional[datetime] = None