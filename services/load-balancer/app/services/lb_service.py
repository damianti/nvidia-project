from fastapi import Request, HTTPException
import json
import logging

from app.services.container_pool import ContainerPool
from app.services.website_mapping import WebsiteMapping
from app.utils.config import TARGET_HOST, SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

async def handle_request(request: Request, website_map: WebsiteMapping, pool:ContainerPool)-> dict:
    body = await request.body()
    data = json.loads(body)
    website_url = data["website_url"].strip().lower()
    logger.info(
        "lb.route.received",
        extra={
            "website_url": website_url,
        }
    )
    image_id = website_map.get_image_id(website_url)
    if image_id is None:
        logger.error(
            "lb.route.image_not_found",
            extra={
                "website_url": website_url,
            }
        )
        raise HTTPException(status_code=404, detail="No image found for this website")
    
    container = pool.get_next_container(image_id)
    if not container:
        logger.warning(
            "lb.route.no_containers",
            extra={
                "image_id": image_id,
                "website_url": website_url,
            }
        )
        raise HTTPException(status_code=503, detail="No running containers available for this website")
    
    logger.info(
        "lb.route.resolved",
        extra={
            "website_url": website_url,
            "image_id": image_id,
            "container_id": container.container_id,
            "target_host": TARGET_HOST,
            "target_port": container.external_port,
            "ttl": 10,
        }
    )
    
    return {
        "target_host": TARGET_HOST,
        "target_port": container.external_port,
        "container_id": container.container_id,
        "image_id": image_id,
        "ttl": 10
    }
    