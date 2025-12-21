from sqlalchemy import Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Location(Base):
    __tablename__ = "location_entries"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    country = Column(String(128), nullable=True)
    state = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="locations")

    def __repr__(self):
        return f"<Location id={self.id} lat={self.latitude} lon={self.longitude}>"
