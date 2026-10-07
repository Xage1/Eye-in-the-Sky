"""
app/models/jwst_request.py

Tracks a user's request for a processed JWST image: the search they
entered, the resolved MAST product, and the background job's progress
through download -> process -> completed (or failed).

Also doubles as a dedup cache: before starting a new download, the
Celery task checks for an existing completed request with the same
mast_product_uri and reuses its preview image instead of re-downloading
from MAST.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class JWSTRequestStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JWSTRequest(Base):
    __tablename__ = "jwst_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What the user searched for, kept verbatim for the user's own history/gallery.
    search_target = Column(String, nullable=True)
    search_proposal_id = Column(String, nullable=True)
    search_instrument = Column(String, nullable=True)

    # The specific MAST product the user picked from search results.
    # Unique per real downloadable file; used for the dedup cache lookup.
    mast_product_uri = Column(String, nullable=False, index=True)
    mast_obs_id = Column(String, nullable=True)
    target_name = Column(String, nullable=True)
    instrument_name = Column(String, nullable=True)

    status = Column(
        Enum(JWSTRequestStatus, name="jwst_request_status"),
        default=JWSTRequestStatus.pending,
        nullable=False,
    )
    error_message = Column(Text, nullable=True)

    fits_path = Column(String, nullable=True)
    preview_image_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="jwst_requests")
