from fastapi import APIRouter, Request, Depends
import logging

from app.services.service_discovery_client import ServiceDiscoveryClient
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



@router.get("/", summary="Route HTTP request Load Balancer Metrics")
async def route_image(
    request: Request,
    
):
    """"""
    pass
