import logging
import httpx
from typing import Dict, List, Optional, Any

from app.utils.config import CONSUL_HOST, SERVICE_NAME
from app.schemas.container_data import ContainerEventData

logger = logging.getLogger(SERVICE_NAME)


async def register_service(container_info: ContainerEventData) -> bool:
    """
    Register a container as a service in Consul with health checks.

    Args:
        container_info: Dictionary containing container details from Kafka event
            - container_id: Unique container ID
            - container_name: Human-readable name
            - container_ip: Internal IP address of the container
            - image_id: Image ID for tagging
            - internal_port: Port exposed by the container (usually 80)
            - external_port: Port mapped on docker-dind host
            - app_hostname: App hostname for tagging

    Returns:
        bool: True if registration successful, False otherwise
    """
    try:
        # Use TCP check since we don't know if containers have /health endpoint
        # TCP check is more reliable as it just verifies the port is open
        # IMPORTANT: Use docker-dind:external_port instead of container_ip:internal_port
        # because Consul cannot access the internal container IP directly.
        # The external_port is mapped on the docker-dind host and accessible from nvidia-network.
        service_data = {
            "ID": container_info.container_id,
            "Name": "webapp-service",  # Common name for all web containers
            "Address": container_info.container_ip,
            "Port": container_info.internal_port,
            "Tags": [
                f"image-{container_info.image_id}",
                f"container-{container_info.container_name}",
                f"external-port-{container_info.external_port}",  # Add external_port to tags for reference
            ],
            "Check": {
                "TCP": f"docker-dind:{container_info.external_port}",  # Use docker-dind hostname + external_port
                "Interval": "10s",
                "Timeout": "2s",
                "DeregisterCriticalServiceAfter": "60s",
            },
        }

        service_data["Tags"].append(f"app-hostname-{container_info.app_hostname}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.put(
                f"{CONSUL_HOST}/v1/agent/service/register", json=service_data
            )

            if response.status_code == 200:
                logger.info(
                    "consul.service_registered",
                    extra={
                        "container_id": container_info.container_id,
                        "container_name": container_info.container_name,
                        "container_ip": container_info.container_ip,
                        "internal_port": container_info.internal_port,
                        "external_port": container_info.external_port,
                        "health_check": f"docker-dind:{container_info.external_port}",
                    },
                )
                return True
            else:
                logger.error(
                    "consul.register_failed",
                    extra={
                        "container_id": container_info.container_id,
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )
                return False

    except Exception as e:
        logger.error(
            "consul.register_error",
            extra={
                "container_id": container_info.container_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return False


async def deregister_service(container_id: str) -> bool:
    """
    Deregister a service from Consul.

    Args:
        container_id: The container ID to deregister

    Returns:
        bool: True if deregistration successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.put(
                f"{CONSUL_HOST}/v1/agent/service/deregister/{container_id}"
            )

            if response.status_code == 200:
                logger.info(
                    "consul.service_deregistered", extra={"container_id": container_id}
                )
                return True
            else:
                logger.error(
                    "consul.deregister_failed",
                    extra={
                        "container_id": container_id,
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )
                return False

    except Exception as e:
        logger.error(
            "consul.deregister_error",
            extra={
                "container_id": container_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return False


async def query_healthy_services(
    service_name: str = "webapp-service", tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Query Consul for healthy services.

    Args:
        service_name: Name of the service to query (default: "webapp-service")
        tags: Optional list of tags to filter by

    Returns:
        List of dictionaries containing service information:
        - container_id: Service ID
        - address: IP address
        - port: Port number
        - status: Health check status
        - tags: Service tags
    """
    try:
        services = []

        if tags:
            # Query for each tag
            for tag in tags:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{CONSUL_HOST}/v1/health/service/{service_name}",
                        params={"passing": "true", "tag": tag},
                    )

                    if response.status_code == 200:
                        for entry in response.json():
                            service_info = {
                                "container_id": entry["Service"]["ID"],
                                "address": entry["Service"]["Address"],
                                "port": entry["Service"]["Port"],
                                "status": (
                                    entry["Checks"][0]["Status"]
                                    if entry["Checks"]
                                    else "unknown"
                                ),
                                "tags": entry["Service"]["Tags"],
                            }
                            services.append(service_info)
        else:
            # Query all services without tag filter
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{CONSUL_HOST}/v1/health/service/{service_name}",
                    params={"passing": "true"},
                )

                if response.status_code == 200:
                    for entry in response.json():
                        service_info = {
                            "container_id": entry["Service"]["ID"],
                            "address": entry["Service"]["Address"],
                            "port": entry["Service"]["Port"],
                            "status": (
                                entry["Checks"][0]["Status"]
                                if entry["Checks"]
                                else "unknown"
                            ),
                            "tags": entry["Service"]["Tags"],
                        }
                        services.append(service_info)

        logger.info(
            "consul.query_successful",
            extra={
                "service_name": service_name,
                "tags": tags,
                "services_found": len(services),
            },
        )

        return services

    except Exception as e:
        logger.error(
            "consul.query_error",
            extra={
                "service_name": service_name,
                "tags": tags,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return []
