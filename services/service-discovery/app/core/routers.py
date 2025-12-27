"""Router configuration."""

from fastapi import FastAPI

from app.api.services import router as services_router


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(services_router, tags=["services"])
