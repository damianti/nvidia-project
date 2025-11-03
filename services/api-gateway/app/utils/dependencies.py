# FastAPI Dependencies
from fastapi import Request, HTTPException
import httpx

from app.services.routing_cache import Cache
from app.clients.lb_client import LoadBalancerClient
from app.clients.orchestrator_client import OrchestratorClient


def get_from_app_state(
    request: Request,
    attr_name: str,
    error_message: str,
    expected_type: type = None
) -> any:
    """
    Generic dependency to get any attribute from app state.
    
    Args:
        request: FastAPI request object
        attr_name: Name of the attribute in app.state
        error_message: Error message if attribute not found
        expected_type: Optional type hint for validation
        
    Returns:
        The attribute from app.state
        
    Raises:
        HTTPException: If attribute not found or wrong type
    """
    value = getattr(request.app.state, attr_name, None)
    if value is None:
        raise HTTPException(status_code=500, detail=error_message)
    
    if expected_type and not isinstance(value, expected_type):
        raise HTTPException(
            status_code=500,
            detail=f"{error_message} (wrong type: expected {expected_type.__name__}, got {type(value).__name__})"
        )
    
    return value


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Dependency to get HTTP client from app state"""
    http_client = getattr(request.app.state, "http_client", None)
    if not http_client:
        # Fallback: create temporary client if not available
        return httpx.AsyncClient(follow_redirects=True)
    return http_client


def get_cached_memory(request: Request) -> Cache:
    """Dependency to get routing cache from app state"""
    return get_from_app_state(
        request=request,
        attr_name="cached_memory",
        error_message="Cached memory not initialized",
        expected_type=Cache
    )


def get_lb_client(request: Request) -> LoadBalancerClient:
    """Dependency to get Load Balancer client from app state"""
    return get_from_app_state(
        request=request,
        attr_name="lb_client",
        error_message="Load Balancer Client not initialized",
        expected_type=LoadBalancerClient
    )


def get_orchestrator_client(request: Request) -> OrchestratorClient:
    """Dependency to get Orchestrator client from app state"""
    return get_from_app_state(
        request=request,
        attr_name="orchestrator_client",
        error_message="Orchestrator Client not initialized",
        expected_type=OrchestratorClient
    )
