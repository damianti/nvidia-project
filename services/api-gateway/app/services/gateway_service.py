# Gateway Service - High-level orchestration for gateway operations
import httpx
import logging
from typing import Optional
from fastapi import Request, Response

from app.services.routing_cache import Cache, CacheEntry
from app.services.routing_service import resolve_route
from app.services.proxy_service import proxy_to_container
from app.utils.http_utils import extract_client_ip, normalize_website_url, prepare_proxy_headers
from app.clients.lb_client import LoadBalancerClient

logger = logging.getLogger("api-gateway")


class RouteValidationError(Exception):
    """Raised when route validation fails"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def validate_and_extract_host(request: Request) -> str:
    """
    Validates Host header and extracts normalized website URL.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Normalized website URL
        
    Raises:
        RouteValidationError: If Host header is missing or invalid
    """
    host_header = request.headers.get("Host", "").strip().lower()
    if not host_header:
        raise RouteValidationError("Missing Host header", status_code=400)
    
    website_url = normalize_website_url(host_header)
    if not website_url:
        raise RouteValidationError("Invalid Host header", status_code=400)
    
    return website_url


async def handle_route_request(
    request: Request,
    http_client: httpx.AsyncClient,
    cached_memory: Cache,
    lb_client: LoadBalancerClient
) -> Response:
    """
    Handle a route request end-to-end.
    
    This function orchestrates:
    1. Host header validation
    2. Client IP extraction
    3. Route resolution (cache + LB)
    4. Request preparation
    5. Proxy to container
    
    Args:
        request: FastAPI request object
        http_client: HTTP client for proxying
        cached_memory: Cache instance
        lb_client: Load Balancer client
        
    Returns:
        FastAPI Response
        
    Raises:
        RouteValidationError: If validation fails
    """
    # Validate Host header and extract website URL
    website_url = validate_and_extract_host(request)
    
    # Extract client IP
    client_ip = extract_client_ip(request)
    
    # Resolve route (checks cache, queries LB if needed)
    entry = await resolve_route(website_url, client_ip, cached_memory, lb_client)
    
    if not entry:
        logger.warning(
            "gateway.route.not_found",
            extra={
                "website_url": website_url,
                "client_ip": client_ip
            }
        )
        return Response(
            content="Website not found or no containers available",
            status_code=503
        )
    
    # Prepare request for proxying
    headers = prepare_proxy_headers(request)
    body = await request.body()
    
    # Proxy to container
    return await proxy_to_container(
        http_client=http_client,
        method=request.method,
        target_host=entry.target_host,
        target_port=entry.target_port,
        headers=headers,
        body=body,
        cached_memory=cached_memory,
        website_url=website_url,
        client_ip=client_ip
    )

