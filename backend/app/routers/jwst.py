"""
app/routers/jwst.py

James Webb Space Telescope (JWST) premium feature.
Free-text search against MAST, background download + visualization
of the Stage-3 mosaic (I2D) product, gated behind Pro/Premium.

Endpoints:
  POST /jwst/search        - free-text target search (Pro/Premium)
  POST /jwst/images        - request a product be downloaded + processed
  GET  /jwst/images/{id}   - poll status of a request (owner or admin)
  GET  /jwst/images        - list current user's requests
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User, UserRole
from app.models.jwst_request import JWSTRequest, JWSTRequestStatus
from app.schemas.jwst import (
    JWSTSearchRequest, JWSTSearchResult,
    JWSTImageRequestCreate, JWSTRequestOut,
)
from app.services.jwst_service import search_jwst_targets
from app.tasks.jwst_tasks import process_jwst_request
from app.utils.deps import get_db, require_pro

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jwst", tags=["JWST"])


@router.post("/search", response_model=list[JWSTSearchResult])
async def search_jwst(
    payload: JWSTSearchRequest,
    current_user: User = Depends(require_pro),
):
    try:
        results = await run_in_threadpool(search_jwst_targets, payload.target, payload.radius_deg)
    except Exception as exc:
        logger.error("JWST search failed | target=%s error=%s", payload.target, exc)
        raise HTTPException(status_code=502, detail="MAST search failed - please try again")

    if not results:
        raise HTTPException(status_code=404, detail=f"No JWST mosaic products found for '{payload.target}'")

    return results


@router.post("/images", response_model=JWSTRequestOut, status_code=status.HTTP_201_CREATED)
async def request_jwst_image(
    payload: JWSTImageRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    result = await db.execute(
        select(JWSTRequest).where(
            JWSTRequest.mast_product_uri == payload.product_uri,
            JWSTRequest.status == JWSTRequestStatus.completed,
        )
    )
    existing = result.scalars().first()
    if existing:
        return existing

    req = JWSTRequest(
        user_id=current_user.id,
        search_target=payload.target_name,
        search_proposal_id=payload.proposal_id,
        search_instrument=payload.instrument_name,
        mast_product_uri=payload.product_uri,
        mast_obs_id=payload.obsid,
        target_name=payload.target_name,
        instrument_name=payload.instrument_name,
        status=JWSTRequestStatus.pending,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    process_jwst_request.delay(req.id)

    return req


@router.get("/images/{request_id}", response_model=JWSTRequestOut)
async def get_jwst_image_status(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    result = await db.execute(select(JWSTRequest).where(JWSTRequest.id == request_id))
    req = result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your request")
    return req


@router.get("/images", response_model=list[JWSTRequestOut])
async def list_jwst_images(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_pro),
):
    result = await db.execute(
        select(JWSTRequest)
        .where(JWSTRequest.user_id == current_user.id)
        .order_by(JWSTRequest.created_at.desc())
    )
    return result.scalars().all()
