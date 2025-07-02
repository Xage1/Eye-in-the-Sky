from pydantic import BaseModel

class Location(BaseModel):
    latitude: float
    longitude: float

class LocationCreate(Location):
    pass