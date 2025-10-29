from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException
import os
import httpx
from urllib.parse import urlencode

from app.services.container_pool import ContainerPool
client = httpx.AsyncClient(follow_redirects=True)

load_dotenv()


router = APIRouter(tags=["load_balancer"])


def get_pool_from_app(request: Request) -> ContainerPool:
    pool = getattr(request.app.state, "container_pool", None)
    if pool is None:
        raise HTTPException(status_code=500, detail="Container pool not initialized")
    return pool


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

    
