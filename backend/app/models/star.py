from sqlalchemy import Column, Integer, String, Float, Index
from app.database import Base


class Star(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True)
    catalog_id = Column(Integer, unique=True, nullable=False)

    proper_name = Column(String, nullable=False)
    bayer_designation = Column(String, nullable=True)

    constellation = Column(String, nullable=False)
    iau_abbreviation = Column(String, nullable=True)

    ra = Column(String, nullable=False)
    dec = Column(String, nullable=False)

    magnitude = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_star_proper_name", "proper_name"),
        Index("ix_star_constellation", "constellation"),
    )