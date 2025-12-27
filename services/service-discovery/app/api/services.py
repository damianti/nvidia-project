from fastapi import APIRouter, Request, Query, HTTPException
from typing import List

from app.utils.config import SERVICE_NAME
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo
from app.utils.logger import setup_logger

logger = setup_logger(SERVICE_NAME)
router = APIRouter(prefix="/services", tags=["services"])


@router.get(
    "/healthy",
    response_model=dict,
    status_code=200,
    summary="Get healthy services",
    description="""
    Get healthy services from Consul cache.
    
    Service Discovery maintains an in-memory cache updated via Consul Watch API.
    This endpoint returns data from the cache for very fast lookups.
    
    Optionally filter by `app_hostname` to get services for a specific application.
    """,
    responses={
        200: {
            "description": "List of healthy services retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "services": [
                            {
                                "image_id": 1,
                                "app_hostname": "myapp.localhost",
                                "host": "localhost",
                                "port": 30001,
                                "status": "healthy"
                            }
                        ],
                        "count": 1,
                        "filters": {"app_hostname": "myapp.localhost"}
                    }
                }
            },
        },
        503: {
            "description": "Service cache not yet initialized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Service cache not yet initialized. Please wait a few seconds."
                    }
                }
            },
        },
    },
)
async def get_healthy_services(
    request: Request,
    app_hostname: str = Query(None, description="Filter services by app hostname"),
):
    """
    Get healthy services from Consul cache.
    
    Args:
        request: FastAPI request object (used to access app state)
        app_hostname: Optional filter by application hostname
    
    Returns:
        dict: List of healthy services with count and filters
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


@router.get(
    "/cache/status",
    response_model=dict,
    status_code=200,
    summary="Get cache status",
    description="Get cache status and statistics for debugging and monitoring purposes.",
    responses={
        200: {
            "description": "Cache status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_services": 10,
                        "last_update": "2024-01-01T00:00:00Z",
                        "cache_size": 10
                    }
                }
            },
        },
    },
)
async def get_cache_status(request: Request):
    """
    Get cache status and statistics.
    
    Returns information about the service cache including:
    - Total number of services in cache
    - Last update timestamp
    - Cache size
    
    Args:
        request: FastAPI request object (used to access app state)
    
    Returns:
        dict: Cache status and statistics
    """
    service_cache: ServiceCache = request.app.state.service_cache
    return service_cache.get_cache_status()
