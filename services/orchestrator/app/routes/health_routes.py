from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="Root endpoint",
    description="Returns basic information about the Orchestrator service.",
    response_description="Service information including version and available endpoints.",
)
async def root():
    """
    Root endpoint that returns basic service information.

    Returns:
        dict: Service metadata including name, version, and available endpoints
    """
    return {
        "message": "NVIDIA Orchestrator with Service Discovery and Message Queue",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "images": "/api/images",
            "containers": "/api/containers",
        },
    }
