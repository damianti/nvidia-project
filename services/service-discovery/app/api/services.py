from fastapi import APIRouter, Request, Query, HTTPException
import logging
from typing import List

from app.utils.config import SERVICE_NAME
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(prefix="/services", tags=["services"])

@router.get("/healthy", response_model=dict)
async def get_healthy_services(
    request: Request,
    website_url: str = Query(None, description="Filter by website URL")
):
    """
    Get healthy services from Consul.
    
    Service Discovery maintains cache updated via Watch API.
    This endpoint returns data from the cache (very fast).
    """
    service_cache : ServiceCache = request.app.state.service_cache

    if service_cache._last_update is None:
        raise HTTPException(
            status_code=503,
            detail="Service cache not yet initialized. Please wait a few seconds."
        )
    services : List[ServiceInfo] = service_cache.get_services(website_url=website_url)
    return {
        "services": [service.model_dump() for service in services],
        "count": len(services),
        "filters": {
            "website_url": website_url
        }
    }

@router.get("/cache/status")
async def get_cache_status(request: Request):
    """
    Get cache status (for debugging)
    """
    service_cache : ServiceCache = request.app.state.service_cache
    return service_cache.get_cache_status()