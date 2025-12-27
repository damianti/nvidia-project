from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="Root endpoint",
    description="Returns basic information about the Load Balancer service.",
    response_description="Service information including version and available endpoints.",
)
async def root():
    """
    Root endpoint that returns basic service information.

    Returns:
        dict: Service metadata including name, version, and available endpoints
    """
    return {
        "message": "NVIDIA Load Balancer",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "route": "POST /route - Route request to container by app_hostname",
            "metrics": "GET /metrics - Get load balancer metrics",
        },
    }
