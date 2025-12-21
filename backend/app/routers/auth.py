# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import SessionLocal
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.user import UserOut
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token
from app.utils.deps import get_db, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ----- Schemas -----
class SignupIn(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----- POST /auth/signup -----
@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupIn, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),  # match model
        name=payload.name
    )

    # Attach default settings (one-to-one)
    user.settings = UserSettings()  # defaults: dark_mode=False, default_difficulty="simple", notifications_enabled=True

    # Save user + settings
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Return JWT token
    token = create_access_token(subject=str(user.id))
    return {"access_token": token}


# ----- POST /auth/login -----
@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return {"access_token": token}


# ----- GET /auth/me -----
@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user