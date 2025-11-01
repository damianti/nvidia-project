from fastapi import APIRouter, Request, HTTPException, Depends
import os
import httpx
import json
import logging
from app.services.container_pool import ContainerPool
from app.services.website_mapping import WebsiteMapping


client = httpx.AsyncClient(follow_redirects=True)
logger = logging.getLogger(__name__)



router = APIRouter(tags=["load_balancer"])


def get_pool_from_app(request: Request) -> ContainerPool:
    pool = getattr(request.app.state, "container_pool", None)
    if pool is None:
        raise HTTPException(status_code=500, detail="Container pool not initialized")
    return pool

def get_map_from_app(request: Request) -> WebsiteMapping:
    website_mp = getattr(request.app.state, "website_map", None)
    if website_mp is None:
        raise HTTPException(status_code=500, detail="website map not initialized")
    return website_mp


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/pool")
async def get_pool_status(request: Request):
    pool = get_pool_from_app(request)
    return pool.get_pool_status()


@router.get("/route/{image_id}")
async def route_image(image_id: int, request: Request):
    """Return next running container info for an image.
    For now, we return the target host/port so the API Gateway can proxy.
    """
    pool = get_pool_from_app(request)
    selected = pool.get_next_container(image_id)
    if not selected:
        raise HTTPException(status_code=503, detail="No running containers available for this image")

    # In this setup containers run inside docker-dind; reach them via its hostname
    target_host = os.getenv("TARGET_HOST", "docker-dind")
    return {
        "image_id": image_id,
        "container_id": selected.container_id,
        "target_host": target_host,
        "target_port": selected.external_port,
    }

    
@router.post("/route")
async def route_image(
    request: Request,
    website_map: WebsiteMapping = Depends(get_map_from_app),
    pool: ContainerPool = Depends(get_pool_from_app)
):  
    body = await request.body()
    data = json.loads(body)
    website_url = data["website_url"].strip().lower()
    logger.info(f"POST /route received - website_url: '{website_url}'")

    image_id = website_map.get_image_id(website_url)
    if image_id is None:
        logger.error(f"Image not found for website {website_url}")
        raise HTTPException(status_code=404, detail="No image found for this website")
    
    container = pool.get_next_container(image_id)
    if not container:
        logger.warning(f"No running containers available for image {image_id}")
        raise HTTPException(status_code=503, detail="No running containers available for this website")
    
    # Los containers están corriendo dentro de docker-dind.
    # Desde nvidia-network, accedemos a ellos a través de docker-dind usando el puerto externo.
    # Los puertos están expuestos solo dentro de docker-dind (no públicamente en el host).
    target_host = os.getenv("TARGET_HOST", "docker-dind")
    res = {
        "target_host": target_host,  # docker-dind (donde están corriendo los containers)
        "target_port": container.external_port,  # Puerto externo expuesto por Docker dentro de docker-dind
        "container_id": container.container_id,
        "image_id": image_id,
        "ttl": 10
    }
    return res

    



