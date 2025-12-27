from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.utils.config import SERVICE_NAME
from app.schemas.billing import BillingSummaryResponse, BillingDetailResponse
from app.schemas.common import ErrorResponse
from app.database.config import get_db
from app.utils.dependencies import get_user_id
from app.services.billing_service import get_all_billing_summaries, get_billing_summary
from app.repositories.usage_repository import get_by_user_and_image
from app.utils.logger import setup_logger

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["billing"])


@router.get(
    "/images",
    response_model=List[BillingSummaryResponse],
    status_code=200,
    summary="Get billing summaries",
    description="Get billing summaries for all images of the authenticated user. Returns aggregated costs per image.",
    responses={
        200: {
            "description": "Billing summaries retrieved successfully",
            "model": List[BillingSummaryResponse],
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    },
)
async def get_user_billings(
    db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Get billing summary for all images of the authenticated user.

    Returns a list of billing summaries, one per image, with aggregated costs.

    Args:
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        List[BillingSummaryResponse]: List of billing summaries per image
    """
    try:
        summaries = get_all_billing_summaries(db, user_id)
        logger.info(
            "billing.summaries_retrieved",
            extra={"user_id": user_id, "image_count": len(summaries)},
        )
        return summaries
    except Exception as e:
        logger.error(
            "billing.summaries_retrieval_failed",
            extra={"user_id": user_id, "error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve billing summaries"
        )


@router.get(
    "/images/{image_id}",
    response_model=BillingDetailResponse,
    status_code=200,
    summary="Get detailed billing",
    description="Get detailed billing information for a specific image. Includes summary and list of all container usage records.",
    responses={
        200: {
            "description": "Billing details retrieved successfully",
            "model": BillingDetailResponse,
        },
        404: {
            "description": "Image not found or does not belong to user",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    },
)
async def get_image_billing(
    image_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)
):
    """
    Get detailed billing information for a specific image.

    Returns detailed billing including summary and list of all container usage records.

    Args:
        image_id: Image identifier
        db: Database session (injected)
        user_id: Authenticated user ID (from token, injected)

    Returns:
        BillingDetailResponse: Detailed billing information with container usage records
    """
    try:
        # Verify that the user has access to this image
        records = get_by_user_and_image(db, user_id, image_id)
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"No billing records found for image {image_id} or image does not belong to user",
            )

        detail = get_billing_summary(db, user_id, image_id)
        logger.info(
            "billing.detail_retrieved",
            extra={
                "user_id": user_id,
                "image_id": image_id,
                "container_count": len(detail.containers),
            },
        )
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "billing.detail_retrieval_failed",
            extra={
                "user_id": user_id,
                "image_id": image_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve billing detail")
