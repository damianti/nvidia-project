from fastapi import APIRouter, Depends
import logging
from typing import List
from sqlalchemy.orm import Session

from app.utils.config import SERVICE_NAME
from app.schemas.billing import BillingSummaryResponse, BillingDetailResponse
from app.database.config import get_db
from app.utils.dependencies import get_user_id

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(tags=["billing"])


@router.get("/images", response_model= List [BillingSummaryResponse])
async def get_user_billings(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Get billing summary for all images of the authenticated user"""
    pass

@router.get("/images/{image_id}", response_model=BillingDetailResponse)
async def get_image_billing(
    image_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Get detailed billing for a specific image"""
    pass