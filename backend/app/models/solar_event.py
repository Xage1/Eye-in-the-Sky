"""app/models/solar_event.py — Celestial events"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Float, func
from app.database import Base

class SolarEvent(Base):
    __tablename__ = "solar_events"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(200), nullable=False)
    event_type      = Column(String(80), nullable=False)
    description     = Column(Text, nullable=True)
    start_time      = Column(DateTime(timezone=True), nullable=False)
    end_time        = Column(DateTime(timezone=True), nullable=True)
    peak_time       = Column(DateTime(timezone=True), nullable=True)
    visible_regions = Column(Text, nullable=True)
    min_latitude    = Column(Float, nullable=True)
    max_latitude    = Column(Float, nullable=True)
    zhr             = Column(Integer, nullable=True)
    radiant_ra      = Column(Float, nullable=True)
    radiant_dec     = Column(Float, nullable=True)
    parent_body     = Column(String(100), nullable=True)
    eclipse_type    = Column(String(50), nullable=True)
    magnitude       = Column(Float, nullable=True)
    source          = Column(String(100), nullable=True)
    is_upcoming     = Column(Boolean, default=True)
    is_notable      = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())