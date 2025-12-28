from fastapi import APIRouter, Request, Query, Depends

from app.services.metrics_collector import MetricsCollector
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache
from app.utils.dependencies import (
    get_metrics_collector,
    get_user_id_cache,
    get_container_user_cache,
    verify_token_and_get_user_id,
)
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["metrics"])


@router.get(
    "/api/metrics",
    summary="Get API Gateway metrics",
    description="""
    Get metrics from the API Gateway for the authenticated user.
    
    Returns aggregated metrics including:
    - Total requests, errors, and average latency for the authenticated user
    - Status code distribution
    - Metrics breakdown by app_hostname and container (only for the authenticated user)
    
    You can optionally filter metrics by providing query parameters:
    - `app_hostname`: Filter metrics for a specific app hostname (must belong to the authenticated user)
    - `container_id`: Filter metrics for a specific container (must belong to the authenticated user)
    
    **Security**: The endpoint automatically filters metrics by the authenticated user's ID.
    Users can only see their own metrics.
    
    Note: Metrics are tracked by app_hostname as it's what arrives directly in requests,
    making it more natural and efficient for API Gateway.
    """,
    response_description="Metrics data",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 1000,
                        "total_errors": 10,
                        "avg_latency_ms": 50.5,
                        "status_codes": {"200": 950, "500": 10},
                        "by_user": {"1": {"requests": 500, "errors": 5, "avg_latency_ms": 45.2}},
                        "by_app_hostname": {"myapp.localhost": {"requests": 300, "errors": 3, "avg_latency_ms": 42.1}},
                        "by_container": {"abc123": {"requests": 100, "errors": 1, "avg_latency_ms": 38.5}},
                    }
                }
            },
        }
    },
)
async def get_metrics(
    request: Request,
    user_id: int = Depends(verify_token_and_get_user_id),
    app_hostname: str = Query(None, description="Filter by app hostname (must belong to authenticated user)"),
    container_id: str = Query(None, description="Filter by container ID (must belong to authenticated user)"),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector),
    user_id_cache: UserIdCache = Depends(get_user_id_cache),
    container_user_cache: ContainerUserCache = Depends(get_container_user_cache),
):
    """
    Get API Gateway metrics for the authenticated user, optionally filtered by app_hostname or container.

    Args:
        request: FastAPI request object (used to access app state)
        user_id: Authenticated user ID (extracted from JWT token)
        app_hostname: Optional filter by app hostname (must belong to authenticated user)
        container_id: Optional filter by container ID (must belong to authenticated user)
        metrics_collector: Metrics collector (injected)
        user_id_cache: Cache for app_hostname -> user_id mapping (used for validation only)
        container_user_cache: Cache for container_id -> user_id mapping (used for validation only)

    Returns:
        dict: Metrics data filtered by authenticated user, optionally filtered by app_hostname or container
    """
    # Validate that app_hostname belongs to the authenticated user
    if app_hostname:
        app_owner_id = user_id_cache.get(app_hostname)
        if app_owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail="You don't have access to metrics for this app_hostname"
            )
    
    # Validate that container_id belongs to the authenticated user
    if container_id:
        container_owner_id = container_user_cache.get(container_id)
        if container_owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail="You don't have access to metrics for this container"
            )
    
    # If filtering by app_hostname or container_id, use those filters
    # Note: Validation already done above, so we can safely filter
    if app_hostname:
        return metrics_collector.get_metrics(app_hostname=app_hostname)
    
    if container_id:
        return metrics_collector.get_metrics(container_id=container_id)
    
    # Otherwise, return metrics filtered by user_id
    return metrics_collector.get_metrics(user_id=user_id)

