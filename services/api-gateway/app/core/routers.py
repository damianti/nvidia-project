"""Router configuration."""

from fastapi import FastAPI

from app.routes import auth_routes, proxy_routes, health_routes, metrics_routes


def setup_routers(app: FastAPI) -> None:
    """Register all application routers.
    
    Order matters: more specific routes must be registered before generic ones.
    For example, /api/metrics must be registered before /api/{path:path}.
    """
    app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
    app.include_router(health_routes.router, tags=["health"])
    app.include_router(metrics_routes.router, tags=["metrics"])  # Must be before proxy_routes
    app.include_router(proxy_routes.router, tags=["proxy"])  # Generic /api/{path:path} comes last
