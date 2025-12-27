from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="Root endpoint",
    description="Returns basic information about the API Gateway service.",
    response_description="Service information including version and available endpoints.",
)
async def root():
    """
    Root endpoint that returns basic service information.

    Returns:
        dict: Service metadata including name, version, and available endpoints
    """
    return {
        "message": "NVIDIA API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
        },
    }


@router.get(
    "/health",
    summary="Health check",
    description="Health check endpoint for monitoring and load balancer health checks.",
    response_description="Service health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "service": "api-gateway"}
                }
            },
        }
    },
)
async def health():
    """
    Health check endpoint.

    Used by monitoring systems and load balancers to verify service availability.

    Returns:
        dict: Health status with service name
    """
    return {"status": "healthy", "service": "api-gateway"}
