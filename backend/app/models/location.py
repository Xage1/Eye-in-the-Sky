from sqlalchemy import Column, Float, Integer, String
from app.database import Base  # if Base is in app/database.py

class LocationEntry(Base):
    __tablename__ = "location_entries"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    country = Column(String(128), nullable=True)
    state = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)

    def __repr__(self):
        return f"<LocationEntry id={self.id} lat={self.latitude} lon={self.longitude}>"