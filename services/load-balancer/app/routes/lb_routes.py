from fastapi import APIRouter, Request, Depends
import logging

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
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])

    
@router.get("/health", summary="Health check endpoint")
async def health():
    """Check if the Load Balancer service is healthy and operational"""
    return {"status": "ok"}


@router.post("/route", summary="Route HTTP request to healthy container instance")
async def route_image(
    request: Request,
    discovery_client: ServiceDiscoveryClient = Depends(get_discovery_client),
    selector: RoundRobinSelector = Depends(get_service_selector),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
    fallback_cache: FallbackCache = Depends(get_fallback_cache),
):
    """Route HTTP request to a healthy container instance using Round Robin selection, Circuit Breaker pattern, and Fallback Cache"""
    return await lb_service.handle_request(
        request=request,
        discovery_client=discovery_client,
        selector=selector,
        circuit_breaker=circuit_breaker,
        fallback_cache=fallback_cache,
    )
    
    

    



