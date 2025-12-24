import asyncio
import httpx
import logging
from typing import List

from app.utils.config import CONSUL_HOST, SERVICE_NAME
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo

logger = logging.getLogger(SERVICE_NAME)


class ConsulWatcher:
    """
    Watcher that performs long polling to Consul to detect changes.
    Automatically updates ServiceCache when there are changes.
    """

    def __init__(self, service_cache: ServiceCache):
        self.service_cache = service_cache
        self.running = False
        self.current_index = 0
        self.service_name = "webapp-service"

    async def start(self):
        """
        Starts the watcher in an infinite loop.
        Performs long polling to Consul and updates cache when there are changes.
        """
        self.running = True
        logger.info("watcher.started", extra={"service_name": self.service_name})

        while self.running:
            try:
                await self._watch_loop()
            except Exception as e:
                logger.error(
                    "watcher.error",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                # Wait before retrying
                await asyncio.sleep(5)

    async def _watch_loop(self):
        """
        Main watch loop.
        Performs long polling to Consul with wait=60s.
        """
        async with httpx.AsyncClient(timeout=65.0) as client:
            url = f"{CONSUL_HOST}/v1/health/service/{self.service_name}"
            params = {
                "passing": "true",  # get only healthy services
                "index": self.current_index,
                "wait": "60s",  # Long polling: wait up to 60s for changes
            }

            try:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    services_data = response.json()
                    new_index = int(response.headers.get("X-Consul-Index", "0"))

                    # Parse services to ServiceInfo
                    services = self._parse_services(services_data)

                    # Update cache
                    await self.service_cache.update_services(services, new_index)

                    self.current_index = new_index

                elif response.status_code == 404:
                    # No services, update cache with empty list
                    await self.service_cache.update_services([], self.current_index)
                    logger.warning("watcher.no_services_found")

                else:
                    logger.error(
                        "watcher.consul_error",
                        extra={
                            "status_code": response.status_code,
                            "response": response.text[:200],
                        },
                    )
                    await asyncio.sleep(5)  # Wait before retrying

            except httpx.TimeoutException:
                # Timeout is normal in long polling (60s without changes)
                # Return and let the loop in start() continue with next request
                logger.debug("watcher.timeout", extra={"note": "No changes in Consul"})
                return

            except httpx.RequestError as e:
                logger.error("watcher.request_error", extra={"error": str(e)})
                await asyncio.sleep(5)  # Wait before retrying

    def _parse_services(self, services_data: list) -> List[ServiceInfo]:
        """
        Parses Consul API response to ServiceInfo objects.

        Args:
            services_data: List of services from Consul API

        Returns:
            List of ServiceInfo objects
        """
        services = []

        for entry in services_data:
            service_info = entry.get("Service", {})
            checks = entry.get("Checks", [])

            # Only services with passing health check
            if not any(check.get("Status") == "passing" for check in checks):
                continue

            tags = service_info.get("Tags", [])

            # Extract metadata from tags
            image_id = self._extract_image_id(tags)
            app_hostname = self._extract_app_hostname(tags)
            external_port = self._extract_external_port(tags)

            # Get health check status
            status = "passing"
            if checks:
                status = checks[0].get("Status", "passing")

            service = ServiceInfo(
                container_id=service_info.get("ID"),
                container_ip=service_info.get("Address"),
                internal_port=service_info.get("Port"),
                external_port=external_port,
                status=status,
                tags=tags,
                image_id=image_id,
                app_hostname=app_hostname,
            )

            services.append(service)

        return services

    def _extract_image_id(self, tags: List[str]) -> int | None:
        """Extracts image_id from tags (format: 'image-{id}')"""
        for tag in tags:
            if tag.startswith("image-"):
                try:
                    return int(tag.split("-")[1])
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_app_hostname(self, tags: List[str]) -> str | None:
        """Extracts app_hostname from tags (format: 'app-hostname-{hostname}')"""
        for tag in tags:
            if tag.startswith("app-hostname-"):
                return tag.replace("app-hostname-", "", 1)
        return None

    def _extract_external_port(self, tags: List[str]) -> int | None:
        """Extracts external_port from tags (format: 'external-port-{port}')"""
        for tag in tags:
            if tag.startswith("external-port-"):
                try:
                    return int(tag.split("-")[2])
                except (ValueError, IndexError):
                    continue
        return None

    def stop(self):
        """Stops the watcher"""
        self.running = False
        logger.info("watcher.stopped")
