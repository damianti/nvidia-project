# Gateway Service - High-level orchestration for gateway operations
import httpx
import logging
import time
from fastapi import Request, Response

from app.services.routing_cache import Cache
from app.services.routing_service import resolve_route
from app.services.proxy_service import proxy_to_container
from app.utils.http_utils import extract_client_ip, prepare_proxy_headers
from app.clients.lb_client import LoadBalancerClient
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache
from app.services.metrics_collector import MetricsCollector

logger = logging.getLogger("api-gateway")


class RouteValidationError(Exception):
    """Raised when route validation fails"""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def handle_route_request(
    request: Request,
    app_hostname: str,
    remaining_path: str,
    http_client: httpx.AsyncClient,
    cached_memory: Cache,
    lb_client: LoadBalancerClient,
    user_id_cache: UserIdCache,
    container_user_cache: ContainerUserCache,
    metrics_collector: MetricsCollector,
) -> Response:
    """
    Handle a route request end-to-end for a user application.

    The caller is responsible for:
      - Extracting a logical app identifier (app_hostname)
      - Extracting the remaining_path to forward to the container

    Steps:
      1. Extract client IP
      2. Resolve destination (cache + Load Balancer)
      3. Prepare headers and body
      4. Proxy the request to the selected container
    """
    # Track start time for latency calculation
    start_time = time.time()

    # 1) Extract client IP
    client_ip = extract_client_ip(request)

    # 2) Resolve route (checks cache, queries LB if needed)
    entry = await resolve_route(
        app_hostname, client_ip, cached_memory, lb_client, user_id_cache
    )
    if not entry:
        logger.warning(
            "gateway.route.not_found",
            extra={
                "app_hostname": app_hostname,
                "client_ip": client_ip,
            },
        )
        return Response(
            content="Application not found or no containers available",
            status_code=503,
        )

    # Get user_id from entry or cache (entry.user_id may be None if cache was created before user_id_cache was populated)
    user_id = entry.user_id
    if user_id is None:
        user_id = user_id_cache.get(app_hostname)

    # Update container_user_cache if we have both container_id and user_id
    if user_id is not None and entry.container_id:
        container_user_cache.set(entry.container_id, user_id)

    # 3) Prepare request for proxying
    headers = prepare_proxy_headers(request)
    body = await request.body()

    # Ensure remaining_path always starts with "/"
    if not remaining_path.startswith("/"):
        remaining_path = "/" + remaining_path

    # 4) Proxy to container
    response = await proxy_to_container(
        http_client=http_client,
        method=request.method,
        target_host=entry.target_host,
        target_port=entry.target_port,
        headers=headers,
        body=body,
        cached_memory=cached_memory,
        app_hostname=app_hostname,
        client_ip=client_ip,
        remaining_path=remaining_path,
    )

    # Calculate latency after proxying
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics (using app_hostname as it's more natural for API Gateway)
    metrics_collector.record_request(
        status_code=response.status_code,
        latency_ms=latency_ms,
        user_id=user_id,  # Puede ser None
        app_hostname=app_hostname,
        container_id=entry.container_id,
    )

    return response
