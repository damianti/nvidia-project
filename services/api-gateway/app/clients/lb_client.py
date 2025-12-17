import logging
import httpx
from typing import Optional, Dict, Callable

from app.models.routing import RouteResult, RoutingInfo, LbError
from app.utils.logger import correlation_id_var

logger = logging.getLogger("api-gateway")

class LoadBalancerClient:
    def __init__(self, base_url: str, http_client: Optional[httpx.AsyncClient] = None, timeout_s: float = 0.5) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or httpx.AsyncClient(follow_redirects=True)
        self.timeout_s = timeout_s
        # Dispatch map: status_code -> handler method
        self._status_handlers: Dict[int, Callable] = {
            200: self._handle_success,
            404: self._handle_not_found,
            503: self._handle_no_capacity,
        }

    def _build_headers(self) -> dict:
        """Adds X-Correlation-ID reading correlation_id_var"""
        corr_id = correlation_id_var.get()
        return {"X-Correlation-ID": corr_id} if corr_id else {}

    def _handle_success(self, response: httpx.Response, app_hostname: str) -> RouteResult:
        """Handler for status 200: parse JSON and create RoutingInfo"""
        try:
            data = response.json()
            routing_info = RoutingInfo(
                target_host=data["target_host"],
                target_port=int(data["target_port"]),
                container_id=data["container_id"],
                image_id=int(data["image_id"]),
                ttl=int(data.get("ttl", 1800))
            )
            logger.info(
                "lb.route.success",
                extra={
                    "app_hostname": app_hostname,
                    "image_id": routing_info.image_id,
                    "container_id": routing_info.container_id,
                    "target_host": routing_info.target_host,
                    "target_port": routing_info.target_port,
                }
            )
            return RouteResult(ok=True, data=routing_info, status_code=200)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "lb.route.parse_error",
                extra={
                    "app_hostname": app_hostname,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_body": response.text[:500]
                }
            )
            return RouteResult(
                ok=False,
                error=LbError.UNKNOWN,
                status_code=200,
                message=f"Failed to parse response: {str(e)}"
            )

    def _handle_not_found(self, response: httpx.Response, app_hostname: str) -> RouteResult:
        """Handler for status 404: website not found"""
        logger.warning(
            "lb.route.not_found",
            extra={"app_hostname": app_hostname, "status_code": 404}
        )
        return RouteResult(
            ok=False,
            error=LbError.NOT_FOUND,
            status_code=404,
            message="Website not found"
        )

    def _handle_no_capacity(self, response: httpx.Response, app_hostname: str) -> RouteResult:
        """Handler for status 503: no containers available"""
        logger.warning(
            "lb.route.no_capacity",
            extra={"app_hostname": app_hostname, "status_code": 503}
        )
        return RouteResult(
            ok=False,
            error=LbError.NO_CAPACITY,
            status_code=503,
            message="No containers available"
        )

    def _handle_unknown_status(self, response: httpx.Response, app_hostname: str) -> RouteResult:
        """Handler for unexpected status codes"""
        logger.error(
            "lb.route.unexpected_status",
            extra={
                "app_hostname": app_hostname,
                "status_code": response.status_code,
                "response_body": response.text[:500]
            }
        )
        return RouteResult(
            ok=False,
            error=LbError.UNKNOWN,
            status_code=response.status_code,
            message=f"Unexpected status code: {response.status_code}"
        )

    async def route(self, app_hostname: str) -> RouteResult:
        """Route request to Load Balancer and return RouteResult.
        """
        headers = self._build_headers()
        try:
            response = await self.http_client.post(
                url=self.base_url,
                json={"app_hostname": app_hostname},
                headers=headers,
                timeout=self.timeout_s,
            )
            
            # Use dispatch map to get handler for status code
            handler = self._status_handlers.get(response.status_code, self._handle_unknown_status)
            return handler(response, app_hostname)

        except httpx.TimeoutException:
            logger.error(
                "lb.route.timeout",
                extra={"app_hostname": app_hostname, "timeout_s": self.timeout_s}
            )
            return RouteResult(
                ok=False,
                error=LbError.TIMEOUT,
                message=f"Timeout after {self.timeout_s}s"
            )
        except Exception as e:
            logger.error(
                "lb.route.error",
                extra={
                    "app_hostname": app_hostname,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return RouteResult(
                ok=False,
                error=LbError.UNKNOWN,
                message=str(e)
            )
