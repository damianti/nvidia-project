from fastapi import Request, HTTPException

from app.services.service_discovery_client import ServiceDiscoveryClient
from app.services.service_selector import RoundRobinSelector
from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache


def _get_from_state(request: Request, attribute: str, detail: str):
    value = getattr(request.app.state, attribute, None)
    if value is None:
        raise HTTPException(status_code=500, detail=detail)
    return value


def get_discovery_client(request: Request) -> ServiceDiscoveryClient:
    return _get_from_state(
        request,
        "discovery_client",
        "Service discovery client not initialized",
    )


def get_service_selector(request: Request) -> RoundRobinSelector:
    return _get_from_state(
        request,
        "service_selector",
        "Service selector not initialized",
    )


def get_circuit_breaker(request: Request) -> CircuitBreaker:
    return _get_from_state(
        request,
        "circuit_breaker",
        "Circuit breaker not initialized",
    )


def get_fallback_cache(request: Request) -> FallbackCache:
    return _get_from_state(
        request,
        "fallback_cache",
        "Fallback cache not initialized",
    )
