"""Router configuration."""
from fastapi import FastAPI

from app.routes import auth_routes, proxy_routes, health_routes


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
    app.include_router(proxy_routes.router, tags=["proxy"])
    app.include_router(health_routes.router, tags=["health"])

