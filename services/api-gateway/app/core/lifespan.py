from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI

from app.services.routing_cache import Cache
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache
from app.services.metrics_collector import MetricsCollector
from app.clients.lb_client import LoadBalancerClient
from app.clients.orchestrator_client import OrchestratorClient
from app.clients.auth_client import AuthClient
from app.utils.logger import setup_logger
from app.utils.config import (
    AUTH_SERVICE_URL,
    LOAD_BALANCER_URL,
    ORCHESTRATOR_URL,
    SERVICE_NAME,
)
from app.core.background_tasks import start_cache_cleanup_task, stop_cache_cleanup_task

logger = setup_logger(SERVICE_NAME)


def create_clients() -> (
    tuple[httpx.AsyncClient, LoadBalancerClient, OrchestratorClient, AuthClient]
):
    """Create and configure HTTP clients for external services."""
    http_client = httpx.AsyncClient(follow_redirects=True)
    lb_client = LoadBalancerClient(LOAD_BALANCER_URL, http_client)
    orchestrator_client = OrchestratorClient(ORCHESTRATOR_URL, http_client)
    auth_client = AuthClient(AUTH_SERVICE_URL, http_client)
    return http_client, lb_client, orchestrator_client, auth_client


def initialize_app_state(app: FastAPI) -> None:
    """Initialize application state with clients and cache."""
    http_client, lb_client, orchestrator_client, auth_client = create_clients()

    app.state.http_client = http_client
    app.state.lb_client = lb_client
    app.state.orchestrator_client = orchestrator_client
    app.state.auth_client = auth_client

    cache = Cache()
    app.state.cached_memory = cache

    user_id_cache = UserIdCache()
    app.state.user_id_cache = user_id_cache

    container_user_cache = ContainerUserCache()
    app.state.container_user_cache = container_user_cache

    metrics_collector = MetricsCollector()
    app.state.metrics_collector = metrics_collector

    # Start background tasks
    cleanup_task = start_cache_cleanup_task(cache)
    app.state.cleanup_task = cleanup_task


async def cleanup_app_state(app: FastAPI) -> None:
    """Cleanup application state and resources."""
    # Stop background tasks
    if hasattr(app.state, "cleanup_task"):
        await stop_cache_cleanup_task(app.state.cleanup_task)

    # Close HTTP client
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("gateway.starting")
    initialize_app_state(app)
    yield

    # Shutdown
    logger.info("gateway.shutting_down")
    await cleanup_app_state(app)
