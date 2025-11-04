from fastapi import Request, HTTPException

from app.services.container_pool import ContainerPool
from app.services.website_mapping import WebsiteMapping

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
