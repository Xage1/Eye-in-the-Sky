from pydantic import BaseModel

class UserSettingsOut(BaseModel):
    id: int
    user_id: int
    dark_mode: bool
    default_difficulty: str
    notifications_enabled: bool

    class Config:
        orm_mode = True