from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import logging

from app.database.models import BillingStatus
from app.repositories.usage_repository import (
    create_usage_record,
    get_active_by_container_id,
    update_usage_record,
    get_by_user_and_image,
    get_all_by_user,
)
from app.services.usage_calculator import (
    calculate_duration_minutes,
    calculate_cost,
    calculate_estimated_cost,
)
from app.schemas.billing import (
    ContainerEventData,
    BillingSummaryResponse,
    BillingDetailResponse,
    UsageRecordResponse,
)

logger = logging.getLogger("billing")


def process_container_started(db: Session, event_data: ContainerEventData) -> None:
    """
    Process a container.started or container.created event.
    Creates a new active usage record.

    Args:
        db: Database session
        event_data: Event data from Kafka
    """
    if not event_data.user_id:
        logger.warning(
            "billing.event_missing_user_id",
            extra={"event": event_data.event, "container_id": event_data.container_id},
        )
        return

    if not event_data.timestamp:
        logger.warning(
            "billing.event_missing_timestamp",
            extra={"event": event_data.event, "container_id": event_data.container_id},
        )
        # Use current time as fallback
        start_time = datetime.now(timezone.utc)
    else:
        start_time = event_data.timestamp

    # Check if there's already an active record (idempotency)
    existing = get_active_by_container_id(db, event_data.container_id)
    if existing:
        logger.info(
            "billing.record_already_exists",
            extra={
                "container_id": event_data.container_id,
                "existing_record_id": existing.id,
            },
        )
        return

    try:
        create_usage_record(
            db=db,
            user_id=event_data.user_id,
            image_id=event_data.image_id,
            container_id=event_data.container_id,
            start_time=start_time,
        )
        logger.info(
            "billing.record_created",
            extra={
                "container_id": event_data.container_id,
                "user_id": event_data.user_id,
                "image_id": event_data.image_id,
                "start_time": start_time.isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            "billing.record_creation_failed",
            extra={
                "container_id": event_data.container_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


def process_container_stopped(db: Session, event_data: ContainerEventData) -> None:
    """
    Process a container.stopped or container.deleted event.
    Closes the active usage record and calculates cost.

    Args:
        db: Database session
        event_data: Event data from Kafka
    """
    logger.info(
        "billing.processing_stopped_event",
        extra={
            "container_id": event_data.container_id,
            "event": event_data.event,
            "timestamp": (
                event_data.timestamp.isoformat() if event_data.timestamp else None
            ),
            "user_id": event_data.user_id,
            "image_id": event_data.image_id,
        },
    )
    if not event_data.timestamp:
        logger.warning(
            "billing.event_missing_timestamp",
            extra={"event": event_data.event, "container_id": event_data.container_id},
        )
        end_time = datetime.now(timezone.utc)
    else:
        end_time = event_data.timestamp

    active_record = get_active_by_container_id(db, event_data.container_id)

    if not active_record:
        logger.warning(
            "billing.no_active_record_found",
            extra={"container_id": event_data.container_id, "event": event_data.event},
        )
        return

    try:
        duration_minutes = calculate_duration_minutes(
            start_time=active_record.start_time, end_time=end_time
        )
        cost = calculate_cost(duration_minutes=duration_minutes)

        update_usage_record(
            db=db,
            usage_record=active_record,
            end_time=end_time,
            duration_minutes=duration_minutes,
            cost=cost,
        )

        logger.info(
            "billing.record_completed",
            extra={
                "container_id": event_data.container_id,
                "duration_minutes": duration_minutes,
                "cost": cost,
            },
        )
    except Exception as e:
        logger.error(
            "billing.record_completion_failed",
            extra={
                "container_id": event_data.container_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


def get_billing_summary(
    db: Session, user_id: int, image_id: int
) -> BillingDetailResponse:
    """
    Get detailed billing information for a specific image.

    Args:
        db: Database session
        user_id: User ID
        image_id: Image ID

    Returns:
        BillingDetailResponse with summary and list of containers
    """
    records = get_by_user_and_image(db, user_id, image_id)

    if not records:
        # Return empty response
        return BillingDetailResponse(
            image_id=image_id,
            summary=BillingSummaryResponse(
                image_id=image_id,
                total_containers=0,
                total_minutes=0,
                total_cost=0.0,
                active_containers=0,
                last_activity=None,
            ),
            containers=[],
        )

    # Calculate aggregates
    total_containers = len(records)
    total_minutes = 0
    total_cost = 0.0
    active_containers = 0

    # Calculate cost and duration for each record (estimated for active, final for completed)
    containers = []
    for record in records:
        if record.status == BillingStatus.ACTIVE:
            # Calculate estimated cost and duration for active containers
            # Ensure start_time is timezone-aware
            start_time = record.start_time
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            estimated_duration = calculate_duration_minutes(
                start_time, datetime.now(timezone.utc)
            )
            estimated_cost = calculate_estimated_cost(start_time, end_time=None)
            active_containers += 1
            total_minutes += estimated_duration
            total_cost += estimated_cost

            containers.append(
                UsageRecordResponse(
                    id=record.id,
                    container_id=record.container_id,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    duration_minutes=estimated_duration,
                    cost=estimated_cost,
                    status=record.status.value,
                )
            )
        else:
            # Use final cost and duration for completed containers
            total_minutes += record.duration_minutes or 0
            total_cost += record.cost or 0.0

            containers.append(
                UsageRecordResponse(
                    id=record.id,
                    container_id=record.container_id,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    duration_minutes=record.duration_minutes,
                    cost=record.cost,
                    status=record.status.value,
                )
            )

    # Find last activity (max of start_time or end_time)
    last_activity = None
    for record in records:
        if record.end_time:
            if last_activity is None or record.end_time > last_activity:
                last_activity = record.end_time
        else:
            if last_activity is None or record.start_time > last_activity:
                last_activity = record.start_time

    summary = BillingSummaryResponse(
        image_id=image_id,
        total_containers=total_containers,
        total_minutes=total_minutes,
        total_cost=round(total_cost, 2),
        active_containers=active_containers,
        last_activity=last_activity,
    )

    return BillingDetailResponse(
        image_id=image_id, summary=summary, containers=containers
    )


def get_all_billing_summaries(
    db: Session, user_id: int
) -> List[BillingSummaryResponse]:
    """
    Get billing summaries for all images of a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of BillingSummaryResponse (one per image)
    """
    records = get_all_by_user(db, user_id)

    if not records:
        return []

    # Group by image_id
    by_image: dict[int, List] = {}
    for record in records:
        if record.image_id not in by_image:
            by_image[record.image_id] = []
        by_image[record.image_id].append(record)

    # Calculate summary for each image
    summaries = []
    for image_id, image_records in by_image.items():
        total_containers = len(image_records)
        total_minutes = 0
        total_cost = 0.0
        active_containers = 0

        # Calculate cost and duration (estimated for active, final for completed)
        for record in image_records:
            if record.status == BillingStatus.ACTIVE:
                # Calculate estimated cost and duration for active containers
                # Ensure start_time is timezone-aware
                start_time = record.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

                estimated_duration = calculate_duration_minutes(
                    start_time, datetime.now(timezone.utc)
                )
                estimated_cost = calculate_estimated_cost(start_time, end_time=None)
                active_containers += 1
                total_minutes += estimated_duration
                total_cost += estimated_cost
            else:
                # Use final cost and duration for completed containers
                total_minutes += record.duration_minutes or 0
                total_cost += record.cost or 0.0

        # Find last activity
        last_activity = None
        for record in image_records:
            if record.end_time:
                if last_activity is None or record.end_time > last_activity:
                    last_activity = record.end_time
            else:
                if last_activity is None or record.start_time > last_activity:
                    last_activity = record.start_time

        summaries.append(
            BillingSummaryResponse(
                image_id=image_id,
                total_containers=total_containers,
                total_minutes=total_minutes,
                total_cost=round(total_cost, 2),
                active_containers=active_containers,
                last_activity=last_activity,
            )
        )

    # Sort by last_activity (most recent first)
    summaries.sort(key=lambda x: x.last_activity or datetime.min, reverse=True)

    return summaries
