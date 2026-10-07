"""
app/schemas/jwst.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.jwst_request import JWSTRequestStatus


class JWSTSearchRequest(BaseModel):
    target: str
    radius_deg: float = 0.2


class JWSTSearchResult(BaseModel):
    product_uri: str
    filename: str
    obsid: Optional[str] = None
    obs_id: Optional[str] = None
    target_name: Optional[str] = None
    instrument_name: Optional[str] = None
    proposal_id: Optional[str] = None
    calib_level: Optional[int] = None
    size_bytes: Optional[int] = None


class JWSTImageRequestCreate(BaseModel):
    product_uri: str
    filename: str
    obsid: str
    obs_id: Optional[str] = None
    target_name: Optional[str] = None
    instrument_name: Optional[str] = None
    proposal_id: Optional[str] = None


class JWSTRequestOut(BaseModel):
    id: int
    user_id: int
    search_target: Optional[str] = None
    search_proposal_id: Optional[str] = None
    search_instrument: Optional[str] = None
    mast_product_uri: str
    mast_obs_id: Optional[str] = None
    target_name: Optional[str] = None
    instrument_name: Optional[str] = None
    status: JWSTRequestStatus
    error_message: Optional[str] = None
    fits_path: Optional[str] = None
    preview_image_path: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
