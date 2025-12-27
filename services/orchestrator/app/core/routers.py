"""Router configuration."""

from fastapi import FastAPI

from app.api import health, images, containers


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(images.router, prefix="/api/images", tags=["images"])
    app.include_router(containers.router, prefix="/api/containers", tags=["containers"])
