from fastapi import APIRouter, Request, Query
import logging
from typing import Optional

from app.utils.config import SERVICE_NAME
from app.services import service_cache

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(tags=["services"])

@router.get("/services/healthy")
async def get_healthy_services(
    image_id: Optional[int] = Query(None),
    website_url: Optional[str] = Query(None)
):
    """
    Get healthy services from Consul.
    
    Service Discovery mantiene cache actualizado via Watch API.
    Este endpoint retorna datos del cache (muy rápido).
    """
    services = service_cache.get_healthy_services(image_id, website_url)
    return {"services": services}