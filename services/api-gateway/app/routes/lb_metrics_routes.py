"""Proxy routes for Load Balancer metrics. Expose LB metrics via API Gateway for UI/monitoring."""

from fastapi import APIRouter, Depends

from app.clients.lb_client import LoadBalancerClient
from app.utils.dependencies import get_lb_client
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)
router = APIRouter(tags=["metrics"])


@router.get(
    "/api/lb/metrics",
    summary="Get Load Balancer metrics",
    description="Proxies to Load Balancer GET /metrics. Returns request counts, errors, latency and breakdowns by image and app hostname.",
)
async def get_lb_metrics(
    lb_client: LoadBalancerClient = Depends(get_lb_client),
):
    """Get aggregated metrics from the Load Balancer (for dashboards/monitoring)."""
    return await lb_client.get_metrics()


@router.get(
    "/api/lb/metrics/mappings",
    summary="Get Load Balancer hostname→port mappings",
    description="Proxies to Load Balancer GET /metrics/mappings. Returns active app_hostname to external_port mapping.",
)
async def get_lb_mappings(
    lb_client: LoadBalancerClient = Depends(get_lb_client),
):
    """Get current hostname to port mappings from the Load Balancer."""
    return await lb_client.get_mappings()
