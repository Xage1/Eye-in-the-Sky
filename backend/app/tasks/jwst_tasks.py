"""
app/tasks/jwst_tasks.py

Downloads a requested JWST Stage-3 mosaic (I2D) product from MAST,
extracts the science image, stretches it for visualization, and
writes the result back onto the JWSTRequest row.

Runs on the jwst_processing queue -- these are large (100s of MB)
downloads that can take minutes, kept off the default queue.
"""

import logging
from datetime import datetime

from app.worker import celery_app
from app.utils.sync_db import get_sync_session
from app.models.jwst_request import JWSTRequest, JWSTRequestStatus
from app.services.jwst_service import download_and_process

logger = logging.getLogger(__name__)

JWST_DATA_DIR = "/app/jwst_data"


@celery_app.task(
    name="app.tasks.jwst_tasks.process_jwst_request",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def process_jwst_request(self, request_id: int):
    db = get_sync_session()
    try:
        req = db.query(JWSTRequest).filter(JWSTRequest.id == request_id).first()
        if not req:
            logger.error("JWST request %s not found", request_id)
            return {"status": "error", "detail": "request not found"}

        req.status = JWSTRequestStatus.downloading
        db.commit()

        try:
            filename = req.mast_product_uri.split("/")[-1] or f"jwst_{request_id}.fits"
            req.status = JWSTRequestStatus.processing
            db.commit()
            result = download_and_process(
                obsid=req.mast_obs_id,
                filename=filename,
                work_dir=JWST_DATA_DIR,
            )
        except Exception as exc:
            logger.error("JWST download/process failed | request=%s error=%s", request_id, exc)
            req.status = JWSTRequestStatus.failed
            req.error_message = str(exc)[:2000]
            db.commit()
            raise self.retry(exc=exc)

        req.fits_path = result["fits_path"]
        req.preview_image_path = result["preview_path"]
        req.status = JWSTRequestStatus.completed
        req.completed_at = datetime.utcnow()
        db.commit()

        logger.info("JWST request %s completed | preview=%s", request_id, result["preview_path"])
        return {"status": "ok", "request_id": request_id}
    finally:
        db.close()
