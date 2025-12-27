from fastapi import APIRouter, Request
from app.services.metrics_collector import MetricsCollector
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])


@router.get(
    "/",
    summary="Get load balancer metrics",
    description="Get load balancer metrics including request counts, errors, latency, and status codes.",
    response_description="Load balancer metrics",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 1000,
                        "total_errors": 10,
                        "avg_latency_ms": 50.5,
                        "status_codes": {"200": 950, "500": 10},
                    }
                }
            },
        }
    },
)
async def get_metrics(request: Request):
    """
    Get load balancer metrics.

    Returns metrics about the load balancer including:
    - Total requests processed
    - Total errors
    - Average latency
    - Status code distribution

    Args:
        request: FastAPI request object (used to access app state)

    Returns:
        dict: Load balancer metrics
    """
    metrics_collector: MetricsCollector = request.app.state.metrics_collector
    return metrics_collector.get_metrics()
