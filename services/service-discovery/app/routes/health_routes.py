from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Health check endpoint for monitoring and load balancer health checks.",
    response_description="Service health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "healthy"}}},
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
    return {"status": "healthy"}


@router.get(
    "/metrics",
    summary="Service metrics",
    description="Get service metrics including Kafka consumer statistics.",
    response_description="Service metrics",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "messages_processed": 100,
                        "registration_success": 95,
                        "registration_failures": 5,
                    }
                }
            },
        }
    },
)
async def metrics(request: Request):
    """
    Get service metrics.

    Returns metrics about the Kafka consumer including:
    - Total messages processed
    - Successful registrations
    - Failed registrations

    Args:
        request: FastAPI request object (used to access app state)

    Returns:
        dict: Service metrics
    """
    consumer = request.app.state.kafka_consumer
    return {
        "messages_processed": consumer.message_count,
        "registration_success": consumer.registration_success,
        "registration_failures": consumer.registration_failures,
    }
