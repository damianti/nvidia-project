from fastapi import Request, HTTPException
import json
import logging
from typing import Optional

from app.schemas.service_info import ServiceInfo
from app.services.service_discovery_client import (
    ServiceDiscoveryClient,
    ServiceDiscoveryError,
)
from app.services.service_selector import RoundRobinSelector
from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.services.fallback_cache import FallbackCache
from app.utils.config import TARGET_HOST, SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

def normalize_app_hostname(value: str) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()

    if normalized.startswith("https://"):
        normalized = normalized[8:]
    elif normalized.startswith("http://"):
        normalized = normalized[7:]

    for sep in ("/", "?", "#"):
        normalized = normalized.split(sep, 1)[0]

    if normalized.count(":") == 1:
        host, port = normalized.rsplit(":", 1)
        if port.isdigit():
            normalized = host

    return normalized.rstrip("/")

async def _pick_service(
    *,
    app_hostname: str,
    discovery_client: ServiceDiscoveryClient,
    selector: RoundRobinSelector,
    circuit_breaker: CircuitBreaker,
    fallback_cache: FallbackCache,
) -> Optional[ServiceInfo]:
    """
    Select a healthy service instance for the given app hostname.
    
    This function implements a resilient service selection pattern:
    1. Attempts to get services from Service Discovery (protected by Circuit Breaker)
    2. On Circuit Breaker OPEN or Service Discovery errors, falls back to cache
    3. Uses Round Robin selector to distribute load evenly
    
    Args:
        app_hostname: Normalized app hostname to route
        discovery_client: Service Discovery client for querying healthy services
        selector: Round Robin selector for load distribution
        circuit_breaker: Circuit Breaker to protect against cascading failures
        fallback_cache: Cache for last known good service list
    
    Returns:
        ServiceInfo if a service is available, None otherwise
    
    Raises:
        ServiceDiscoveryError: If Service Discovery fails and no fallback cache available
    """
    services = None

    try:
        services = await circuit_breaker.call(
            discovery_client.get_healthy_services,
            app_hostname=app_hostname
        )

        # Success - update fallback cache
        if services:
            await fallback_cache.update(app_hostname, services)
            logger.info(
                "lb.route.discovery_success_cache_updated",
                extra={"app_hostname": app_hostname, "services_count": len(services)}
            )
    
    except CircuitBreakerOpenError:
        # Circuit is OPEN - try fallback cache
        logger.warning(
            "lb.route.circuit_open_using_fallback",
            extra={"app_hostname": app_hostname}
        )
        services = await fallback_cache.get(app_hostname)
        if services:
            logger.info(
                "lb.route.fallback_cache_hit",
                extra={"app_hostname": app_hostname, "services_count": len(services)}
            )
        else:
            logger.error(
                "lb.route.fallback_cache_miss",
                extra={"app_hostname": app_hostname}
            )
    
    except ServiceDiscoveryError as exc:
        # Service Discovery error - try fallback cache
        logger.warning(
            "lb.route.discovery_error_using_fallback",
            extra={
                "app_hostname": app_hostname,
                "error": str(exc)
            }
        )
        services = await fallback_cache.get(app_hostname)
        if services:
            logger.info(
                "lb.route.fallback_cache_hit_after_error",
                extra={"app_hostname": app_hostname, "services_count": len(services)}
            )
        else:
            logger.error(
                "lb.route.fallback_cache_miss_after_error",
                extra={"app_hostname": app_hostname}
            )
            raise  # Re-raise if no fallback available
    
    if not services:
        logger.warning(
            "lb.route.no_services_available",
            extra={"app_hostname": app_hostname}
        )
        return None
    
    image_id = services[0].image_id or 0
    return selector.select(image_id, services)


async def handle_request(
    request: Request,
    discovery_client: ServiceDiscoveryClient,
    selector: RoundRobinSelector,
    circuit_breaker: CircuitBreaker,
    fallback_cache: FallbackCache,
) -> dict:
    """
    Handle a routing request from the API Gateway.
    
    Processes the request to find an available container for the given app hostname.
    Returns routing information (host, port) that the API Gateway can use to proxy requests.
    
    Args:
        request: FastAPI request object containing app_hostname in JSON body
        discovery_client: Service Discovery client
        selector: Round Robin selector
        circuit_breaker: Circuit Breaker instance
        fallback_cache: Fallback cache instance
    
    Returns:
        Dictionary with routing information:
        - target_host: Host where container is running
        - target_port: External port of the container
        - container_id: ID of the selected container
        - image_id: ID of the image
        - ttl: Cache TTL in seconds
    
    Raises:
        HTTPException: 503 if no services available or Service Discovery is down
    """
    # Parse and validate request body
    try:
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=400,
                detail="Request body is required"
            )
        
        data = json.loads(body)
        if "app_hostname" not in data:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: app_hostname"
            )
        
        raw_app_hostname = data["app_hostname"]
        app_hostname = normalize_app_hostname(raw_app_hostname)
        if not app_hostname:
            raise HTTPException(status_code=400, detail="app_hostname cannot be empty")

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        ) from e
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field: {str(e)}"
        ) from e
    
    logger.info(
        "lb.route.received",
        extra={
            "app_hostname": app_hostname,
        },
    )
    
    try:
        service = await _pick_service(
            app_hostname=app_hostname,
            discovery_client=discovery_client,
            selector=selector,
            circuit_breaker=circuit_breaker,
            fallback_cache=fallback_cache,
        )
    except (ServiceDiscoveryError, CircuitBreakerOpenError) as exc:
        logger.error(
            "lb.route.service_unavailable",
            extra={
                "app_hostname": app_hostname,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "circuit_state": circuit_breaker.get_state().value,
            },
        )
        raise HTTPException(
            status_code=503,
            detail="Service discovery is unavailable. Please retry shortly.",
        ) from exc

    if service is None:
        raise HTTPException(
            status_code=503,
            detail="No running containers available for this website",
        )

    external_port = service.external_port
    container_id = service.container_id
    image_id = service.image_id

    logger.info(
        "lb.route.resolved",
        extra={
            "app_hostname": app_hostname,
            "image_id": image_id,
            "container_id": container_id,
            "target_host": TARGET_HOST,
            "target_port": external_port,
            "ttl": 10,
        },
    )

    return {
        "target_host": TARGET_HOST,
        "target_port": external_port,
        "container_id": container_id,
        "image_id": image_id,
        "ttl": 10,
    }
    