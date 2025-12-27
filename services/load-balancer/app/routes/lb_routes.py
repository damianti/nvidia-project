from fastapi import APIRouter, Request, Depends, Response

from app.services.service_discovery_client import ServiceDiscoveryClient
from app.services.service_selector import RoundRobinSelector
from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache
from app.utils.dependencies import (
    get_discovery_client,
    get_service_selector,
    get_circuit_breaker,
    get_fallback_cache,
)
from app.services import lb_service
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])


@router.post(
    "/",
    summary="Route HTTP request",
    description="""
    Route HTTP request to a healthy container instance.
    
    Uses Round Robin selection algorithm to distribute requests evenly across
    available healthy containers. Implements Circuit Breaker pattern for fault
    tolerance and Fallback Cache for degraded service handling.
    
    The request is proxied to the selected container and the response is returned.
    """,
    responses={
        200: {
            "description": "Request routed successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Response from container"}
                }
            },
        },
        503: {
            "description": "No healthy containers available",
            "content": {
                "application/json": {
                    "example": {"detail": "No healthy services available"}
                }
            },
        },
        502: {
            "description": "Bad gateway - container unavailable",
            "content": {
                "application/json": {
                    "example": {"detail": "Service unavailable"}
                }
            },
        },
    },
)
async def route_image(
    request: Request,
    discovery_client: ServiceDiscoveryClient = Depends(get_discovery_client),
    selector: RoundRobinSelector = Depends(get_service_selector),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
    fallback_cache: FallbackCache = Depends(get_fallback_cache),
):
    """
    Route HTTP request to a healthy container instance.
    
    Args:
        request: FastAPI request object
        discovery_client: Service discovery client (injected)
        selector: Service selector for load balancing (injected)
        circuit_breaker: Circuit breaker for fault tolerance (injected)
        fallback_cache: Fallback cache for degraded service (injected)
    
    Returns:
        Response: Proxied response from the selected container
    """
    return await lb_service.handle_request(
        request=request,
        discovery_client=discovery_client,
        selector=selector,
        circuit_breaker=circuit_breaker,
        fallback_cache=fallback_cache,
    )
