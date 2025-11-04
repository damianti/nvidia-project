from fastapi import APIRouter, Request, Depends
import logging

from app.services.container_pool import ContainerPool
from app.services.website_mapping import WebsiteMapping
from app.utils.dependencies import get_pool_from_app, get_map_from_app
from app.services import lb_service
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/pool")
async def get_pool_status(pool: ContainerPool = Depends(get_pool_from_app)):
    return pool.get_pool_status()


@router.post("/route")
async def route_image(
    request: Request,
    website_map: WebsiteMapping = Depends(get_map_from_app),
    pool: ContainerPool = Depends(get_pool_from_app)
):
    return lb_service.handle_request(request, website_map, pool)
    
    

    



