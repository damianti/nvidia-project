from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from sqlalchemy import and_

from app.database.models import Billing, BillingStatus


def create_usage_record(
    db: Session, user_id: int, image_id: int, container_id: str, start_time: datetime
) -> Billing:
    """
    Create a new usage record for a container that just started.

    Args:
        db: Database session
        user_id: User ID who owns the container
        image_id: Image ID
        container_id: Docker container ID (string)
        start_time: When the container started

    Returns:
        Created Billing record
    """
    db_billing = Billing(
        user_id=user_id,
        image_id=image_id,
        container_id=container_id,
        start_time=start_time,
        status=BillingStatus.ACTIVE,
    )
    db.add(db_billing)
    db.commit()
    db.refresh(db_billing)
    return db_billing


def get_active_by_container_id(db: Session, container_id: str) -> Optional[Billing]:
    """
    Get the active usage record for a container.

    Args:
        db: Database session
        container_id: Docker container ID

    Returns:
        Active Billing record or None if not found
    """
    return (
        db.query(Billing)
        .filter(
            and_(
                Billing.container_id == container_id,
                Billing.status == BillingStatus.ACTIVE,
            )
        )
        .first()
    )


def update_usage_record(
    db: Session,
    usage_record: Billing,
    end_time: datetime,
    duration_minutes: int,
    cost: float,
) -> Billing:
    """
    Update a usage record when a container stops.
    Marks it as completed and sets end_time, duration, and cost.

    Args:
        db: Database session
        usage_record: The Billing record to update
        end_time: When the container stopped
        duration_minutes: Calculated duration in minutes
        cost: Calculated cost

    Returns:
        Updated Billing record
    """
    usage_record.end_time = end_time
    usage_record.duration_minutes = duration_minutes
    usage_record.cost = cost
    usage_record.status = BillingStatus.COMPLETED

    db.commit()
    db.refresh(usage_record)
    return usage_record


def get_by_user_and_image(db: Session, user_id: int, image_id: int) -> List[Billing]:
    """
    Get all usage records for a specific user and image.

    Args:
        db: Database session
        user_id: User ID
        image_id: Image ID

    Returns:
        List of Billing records
    """
    return (
        db.query(Billing)
        .filter(and_(Billing.user_id == user_id, Billing.image_id == image_id))
        .order_by(Billing.start_time.desc())
        .all()
    )


def get_all_by_user(db: Session, user_id: int) -> List[Billing]:
    """
    Get all usage records for a user (across all images).

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of Billing records
    """
    return (
        db.query(Billing)
        .filter(Billing.user_id == user_id)
        .order_by(Billing.start_time.desc())
        .all()
    )
