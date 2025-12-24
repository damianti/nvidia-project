from fastapi import APIRouter, Request, Query, HTTPException
import logging
from typing import List

from app.utils.config import SERVICE_NAME
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(prefix="/services", tags=["services"])


@router.get(
    "/healthy", response_model=dict, summary="Get healthy services from Consul cache"
)
async def get_healthy_services(
    request: Request,
    app_hostname: str = Query(None, description="Filter by app hostname"),
):
    """
    Get healthy services from Consul.

    Service Discovery maintains cache updated via Watch API.
    This endpoint returns data from the cache (very fast).
    """
    service_cache: ServiceCache = request.app.state.service_cache

    if service_cache._last_update is None:
        raise HTTPException(
            status_code=503,
            detail="Service cache not yet initialized. Please wait a few seconds.",
        )
    services: List[ServiceInfo] = service_cache.get_services(app_hostname=app_hostname)
    return {
        "services": [service.model_dump() for service in services],
        "count": len(services),
        "filters": {"app_hostname": app_hostname},
    }


@router.get("/cache/status", summary="Get service cache status and statistics")
async def get_cache_status(request: Request):
    """
    Get cache status and statistics for debugging and monitoring purposes
    """
    service_cache: ServiceCache = request.app.state.service_cache
    return service_cache.get_cache_status()
