from pydantic import EmailStr, BaseModel
from typing import Optional
from app.schemas.user_settings import UserSettingsOut


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# User Schema
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    settings: Optional[UserSettingsOut]

    class Config:
        orm_mode= True