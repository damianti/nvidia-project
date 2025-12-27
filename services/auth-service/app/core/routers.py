"""Router configuration."""

from fastapi import FastAPI

from app.api import auth


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
