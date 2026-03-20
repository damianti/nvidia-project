from fastapi import APIRouter, Request
from app.services.metrics_collector import MetricsCollector
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["load_balancer"])


def _get_collector(request: Request) -> MetricsCollector:
    return request.app.state.metrics_collector


@router.get(
    "/",
    summary="Get load balancer metrics",
    description=(
        "Get aggregated load balancer metrics including request counts, errors, "
        "latency and status codes. Also includes breakdowns by image and app hostname "
        "when available."
    ),
    response_description="Load balancer metrics",
)
async def get_metrics(request: Request):
    """Get load balancer metrics (JSON friendly for dashboards)."""
    metrics_collector = _get_collector(request)
    return await metrics_collector.get_metrics()


@router.get(
    "/mappings",
    summary="Get current hostname → port mappings",
    description="Returns the active mapping between app_hostname and external_port in the load balancer.",
    response_description="Active hostname to port mappings",
)
async def get_mappings(request: Request):
    """Get the current app_hostname → external_port mapping."""
    metrics_collector = _get_collector(request)
    return {"active_mappings": await metrics_collector.get_active_mappings()}
