"""Router configuration."""
from fastapi import FastAPI

from app.api.billing import router as billing_router


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(billing_router, tags=["billing"])

