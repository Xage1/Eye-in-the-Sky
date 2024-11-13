from fastapi import APIRouter, Depends, HTTPException, status
from .models import User, SessionLocal, Event
from .utils import calculate_event_visibility
from passlib.context import CryptContext
from pydantic import BaseModel


router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register")
async def register_user(user: UserCreate):
    db = SessionLocal()
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/preferences")
async def get_user_preferences(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    return user.preferences if user else HTTPException(status_code=404, detail="User not found")


@router.get("/events")
async def get_events(date: str):
    # Query events for a given date
    # Return the data in JSON format
    pass

@router.get("/event/{event_id}")
async def get_event_detail(event_id: int):
    # Query and return details of a specific event
    pass