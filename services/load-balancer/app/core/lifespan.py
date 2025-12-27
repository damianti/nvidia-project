from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.service_discovery_client import ServiceDiscoveryClient
from app.services.service_selector import RoundRobinSelector
from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache
from app.services.metrics_collector import MetricsCollector
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        "lb.startup",
        extra={
            "service_name": SERVICE_NAME,
        },
    )

    discovery_client = ServiceDiscoveryClient()
    service_selector = RoundRobinSelector()
    circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=15.0)
    fallback_cache = FallbackCache(ttl_seconds=10.0)
    metrics_collector = MetricsCollector()

    app.state.discovery_client = discovery_client
    app.state.service_selector = service_selector
    app.state.circuit_breaker = circuit_breaker
    app.state.fallback_cache = fallback_cache
    app.state.metrics_collector = metrics_collector

    yield

    # Shutdown
    logger.info(
        "lb.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        },
    )
    await discovery_client.close()
