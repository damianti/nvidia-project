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


async def _pick_service(
    *,
    website_url: str,
    discovery_client: ServiceDiscoveryClient,
    selector: RoundRobinSelector,
    circuit_breaker: CircuitBreaker,
    fallback_cache: FallbackCache,
) -> Optional[ServiceInfo]:
    """
    Pick a service using Service Discovery with Circuit Breaker protection.
    Falls back to cache if Service Discovery is unavailable.
    """
    services = None
    
    # Try to get services from Service Discovery (protected by Circuit Breaker)
    try:
        services = await circuit_breaker.call(
            discovery_client.get_healthy_services,
            website_url=website_url
        )
        
        # Success - update fallback cache
        if services:
            await fallback_cache.update(website_url, services)
            logger.info(
                "lb.route.discovery_success_cache_updated",
                extra={"website_url": website_url, "services_count": len(services)}
            )
    
    except CircuitBreakerOpenError:
        # Circuit is OPEN - try fallback cache
        logger.warning(
            "lb.route.circuit_open_using_fallback",
            extra={"website_url": website_url}
        )
        services = await fallback_cache.get(website_url)
        if services:
            logger.info(
                "lb.route.fallback_cache_hit",
                extra={"website_url": website_url, "services_count": len(services)}
            )
        else:
            logger.error(
                "lb.route.fallback_cache_miss",
                extra={"website_url": website_url}
            )
    
    except ServiceDiscoveryError as exc:
        # Service Discovery error - try fallback cache
        logger.warning(
            "lb.route.discovery_error_using_fallback",
            extra={
                "website_url": website_url,
                "error": str(exc)
            }
        )
        services = await fallback_cache.get(website_url)
        if services:
            logger.info(
                "lb.route.fallback_cache_hit_after_error",
                extra={"website_url": website_url, "services_count": len(services)}
            )
        else:
            logger.error(
                "lb.route.fallback_cache_miss_after_error",
                extra={"website_url": website_url}
            )
            raise  # Re-raise if no fallback available
    
    if not services:
        logger.warning(
            "lb.route.no_services_available",
            extra={"website_url": website_url}
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
    body = await request.body()
    data = json.loads(body)
    website_url = data["website_url"].strip().lower()
    logger.info(
        "lb.route.received",
        extra={
            "website_url": website_url,
        },
    )
    
    try:
        service = await _pick_service(
            website_url=website_url,
            discovery_client=discovery_client,
            selector=selector,
            circuit_breaker=circuit_breaker,
            fallback_cache=fallback_cache,
        )
    except (ServiceDiscoveryError, CircuitBreakerOpenError) as exc:
        logger.error(
            "lb.route.service_unavailable",
            extra={
                "website_url": website_url,
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
            "website_url": website_url,
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
    