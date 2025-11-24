from fastapi import APIRouter, Request, Depends
import logging

from app.services.service_discovery_client import ServiceDiscoveryClient
from app.services.service_selector import RoundRobinSelector
from app.utils.dependencies import (
    get_discovery_client,
    get_service_selector,
)
from app.services import lb_service
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/route")
async def route_image(
    request: Request,
    discovery_client: ServiceDiscoveryClient = Depends(get_discovery_client),
    selector: RoundRobinSelector = Depends(get_service_selector),
):
    return await lb_service.handle_request(
        request=request,
        discovery_client=discovery_client,
        selector=selector,
    )
    
    

    



