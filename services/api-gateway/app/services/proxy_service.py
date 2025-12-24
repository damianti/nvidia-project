# Proxy Service - Business logic for proxying requests
import httpx
import logging
from fastapi import Response

from app.services.routing_cache import Cache

logger = logging.getLogger("api-gateway")


async def proxy_to_target(
    http_client: httpx.AsyncClient,
    method: str,
    target_url: str,
    headers: dict,
    body: bytes,
) -> Response:
    """
    Proxy a request to target URL.

    Args:
        http_client: HTTP client to use for the request
        method: HTTP method (GET, POST, etc.)
        target_url: Target URL to proxy to
        headers: Headers to send with the request
        body: Request body bytes

    Returns:
        FastAPI Response with content, status_code, headers
    """
    try:
        response = await http_client.request(
            method=method, url=target_url, headers=headers, content=body
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.TimeoutException as e:
        logger.error(
            "proxy.timeout",
            extra={"target_url": target_url, "method": method, "error": str(e)},
        )
        return Response(
            content="Request timeout - container may be overloaded", status_code=504
        )
    except httpx.ConnectError as e:
        logger.error(
            "proxy.connection_error",
            extra={"target_url": target_url, "method": method, "error": str(e)},
        )
        return Response(
            content="Cannot connect to container - service may be down", status_code=503
        )
    except Exception as e:
        logger.error(
            "proxy.error",
            extra={
                "target_url": target_url,
                "method": method,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return Response(content="Internal proxy error", status_code=502)


async def proxy_to_container(
    http_client: httpx.AsyncClient,
    method: str,
    target_host: str,
    target_port: int,
    headers: dict,
    body: bytes,
    cached_memory: Cache,
    app_hostname: str,
    client_ip: str,
    remaining_path: str,
) -> Response:
    """
    Proxy request to a specific container.

    Args:
        http_client: HTTP client to use
        method: HTTP method
        target_host: Container host
        target_port: Container port
        headers: Headers to send
        body: Request body
        cached_memory: Cache instance for invalidation
        app_hostname: Logical app identifier (used as cache key)
        client_ip: Client IP for cache invalidation
        remaining_path: Path to forward to the container

    Returns:
        FastAPI Response
    """
    # Ensure remaining_path always has a leading slash
    if not remaining_path.startswith("/"):
        remaining_path = "/" + remaining_path

    target_url = f"http://{target_host}:{target_port}{remaining_path}"

    response = await proxy_to_target(
        http_client=http_client,
        method=method,
        target_url=target_url,
        headers=headers,
        body=body,
    )

    if response.status_code >= 500:
        logger.warning(
            "proxy.container_failed",
            extra={
                "target_url": target_url,
                "app_hostname": app_hostname,
                "client_ip": client_ip,
                "status_code": response.status_code,
            },
        )
        cached_memory.invalidate(app_hostname, client_ip)

    return response
