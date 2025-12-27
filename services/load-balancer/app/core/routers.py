"""Router configuration."""

from fastapi import FastAPI

from app.routes import lb_routes, lb_metrics, lb_health
from app.routes.health_routes import router as root_router


def setup_routers(app: FastAPI) -> None:
    """Register all application routers."""
    app.include_router(root_router, tags=["health"])
    app.include_router(lb_routes.router, prefix="/route", tags=["load_balancer"])
    app.include_router(lb_metrics.router, prefix="/metrics", tags=["load_balancer"])
    app.include_router(lb_health.router, prefix="/health", tags=["health"])
