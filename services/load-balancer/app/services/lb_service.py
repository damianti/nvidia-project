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
from app.utils.config import TARGET_HOST, SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


async def _pick_service(
    *,
    website_url: str,
    discovery_client: ServiceDiscoveryClient,
    selector: RoundRobinSelector,
) -> Optional[ServiceInfo]:
    services = await discovery_client.get_healthy_services(website_url=website_url)
    if not services:
        logger.warning(
            "lb.route.no_services_from_discovery",
            extra={
                "website_url": website_url,
            },
        )
        return None
    image_id = services[0].image_id or 0
    return selector.select(image_id, services)


async def handle_request(
    request: Request,
    discovery_client: ServiceDiscoveryClient,
    selector: RoundRobinSelector,
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
        )
    except ServiceDiscoveryError as exc:
        logger.error(
            "lb.route.discovery_error",
            extra={
                "website_url": website_url,
                "error": str(exc),
                "error_type": type(exc).__name__,
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
    