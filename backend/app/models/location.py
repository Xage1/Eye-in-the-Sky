from sqlalchemy import Column, Float, Integer, String
from app.database import Base 

class LocationEntry(Base):
    __tablename__ = "location_entries"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)