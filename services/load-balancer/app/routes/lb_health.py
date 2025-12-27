from fastapi import APIRouter
from app.utils.config import SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="Health check",
    description="Health check endpoint for monitoring and load balancer health checks.",
    response_description="Service health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
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
        dict: Health status
    """
    return {"status": "ok"}

