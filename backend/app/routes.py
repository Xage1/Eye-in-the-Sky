from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .models import User, Event, get_db
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User created successfully", "user_id": db_user.id}

@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"preferences": user.preferences}

@router.get("/events")
async def get_events(date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Event)
    if date:
        query = query.filter(Event.date == date)
    events = query.all()
    return events

@router.get("/event/{event_id}")
async def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event