import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.schemas.service_info import ServiceInfo
from app.utils.config import SERVICE_DISCOVERY_URL, SERVICE_NAME


logger = logging.getLogger(SERVICE_NAME)


class ServiceDiscoveryError(Exception):
    """Raised when service discovery cannot return healthy services."""


class ServiceDiscoveryClient:
    """
    Thin async client to query the service-discovery API.

    The Load Balancer relies on this client instead of talking directly to Consul.
    """

    def __init__(self, base_url: str = SERVICE_DISCOVERY_URL, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        async with self._lock:
            await self._client.aclose()

    async def get_healthy_services(
        self,
        *,
        website_url: Optional[str] = None,
    ) -> List[ServiceInfo]:
        """
        Fetch healthy services filtered by image_id or website_url.
        """
        params: Dict[str, Any] = {}
        if website_url:
            params["website_url"] = website_url

        logger.info(
            "discovery.fetch_services",
            extra={
                "base_url": self.base_url,
                "params": params,
            },
        )

        try:
            response = await self._client.get(f"{self.base_url}/services/healthy", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "discovery.http_status_error",
                extra={
                    "status_code": exc.response.status_code,
                    "response": exc.response.text[:200],
                },
            )
            raise ServiceDiscoveryError("Service discovery responded with an error") from exc
        except httpx.HTTPError as exc:
            logger.error(
                "discovery.http_error",
                extra={"error": str(exc), "error_type": type(exc).__name__},
            )
            raise ServiceDiscoveryError("Unable to contact service discovery") from exc

        data = response.json()
        payload = data.get("services", [])
        services = [ServiceInfo.model_validate(item) for item in payload]
        logger.info(
            "discovery.services_received",
            extra={
                "count": len(services),
                "website_url": website_url,
            },
        )
        return services

