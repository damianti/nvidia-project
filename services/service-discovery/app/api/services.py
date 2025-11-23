from fastapi import APIRouter, Request, Query, HTTPException
import logging
from typing import Optional, List

from app.utils.config import SERVICE_NAME
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(prefix="/services", tags=["services"])

@router.get("/healthy", response_model=dict)
async def get_healthy_services(
    request: Request,
    image_id: Optional[int] = Query(None, description="Filter by image ID"),
    website_url: Optional[str] = Query(None, description="Filter by website URL")
):
    """
    Get healthy services from Consul.
    
    Service Discovery mantiene cache actualizado via Watch API.
    Este endpoint retorna datos del cache (muy rápido).
    """
    service_cache : ServiceCache = request.app.state.service_cache

    if service_cache._last_update is None:
        raise HTTPException(
            status_code=503,
            detail="Service cache not yet initialized. Please wait a few seconds."
        )
    services : List[ServiceInfo] = service_cache.get_services(
        image_id = image_id,
        website_url = website_url
    )
    return {
        "services": [service.model_dump() for service in services],
        "count": len(services),
        "filters": {
            "image_id": image_id,
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