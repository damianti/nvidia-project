"""
Metrics Collector for Load Balancer.

Tracks request metrics, latency, and port mappings for monitoring and analytics.
State is stored in Redis for distributed consistency across multiple instances.
"""

import logging
from typing import Dict, Any, List

import redis.asyncio as aioredis

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

_GLOBAL_KEY = "lb:metrics:global"
_STATUS_CODES_KEY = "lb:metrics:status_codes"
_MAPPINGS_KEY = "lb:metrics:mappings"


class MetricsCollector:
    """Collects and aggregates metrics for the load balancer, backed by Redis."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def record_request(
        self,
        status_code: int,
        latency_ms: float = 0.0,
        image_id: int = None,
        app_hostname: str = None,
        traffic_bytes: int = 0,
    ) -> None:
        """Record a request with its status code and latency."""
        pipe = self._redis.pipeline()

        pipe.hincrby(_GLOBAL_KEY, "total_requests", 1)
        pipe.hincrby(_STATUS_CODES_KEY, str(status_code), 1)

        if status_code >= 400:
            pipe.hincrby(_GLOBAL_KEY, "total_errors", 1)

        if latency_ms > 0:
            pipe.hincrbyfloat(_GLOBAL_KEY, "latency_sum", latency_ms)
            pipe.hincrby(_GLOBAL_KEY, "latency_count", 1)

        if image_id is not None:
            img_key = f"lb:metrics:image:{image_id}"
            pipe.hincrby(img_key, "requests", 1)
            pipe.hincrby(f"{img_key}:status_codes", str(status_code), 1)
            if status_code >= 400:
                pipe.hincrby(img_key, "errors", 1)
            if latency_ms > 0:
                pipe.hincrbyfloat(img_key, "latency_sum", latency_ms)
                pipe.hincrby(img_key, "latency_count", 1)

        if app_hostname:
            host_key = f"lb:metrics:hostname:{app_hostname}"
            pipe.hincrby(host_key, "requests", 1)
            pipe.hincrby(host_key, "traffic", traffic_bytes)
            pipe.hincrby(f"{host_key}:status_codes", str(status_code), 1)
            if status_code >= 400:
                pipe.hincrby(host_key, "errors", 1)
            if latency_ms > 0:
                pipe.hincrbyfloat(host_key, "latency_sum", latency_ms)
                pipe.hincrby(host_key, "latency_count", 1)

        await pipe.execute()

    async def update_mapping(self, app_hostname: str, external_port: int) -> None:
        """Update the active mapping for an app hostname."""
        await self._redis.hset(_MAPPINGS_KEY, app_hostname, external_port)

    async def remove_mapping(self, app_hostname: str) -> None:
        """Remove the mapping for an app hostname."""
        await self._redis.hdel(_MAPPINGS_KEY, app_hostname)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        global_data = await self._redis.hgetall(_GLOBAL_KEY)
        status_codes_data = await self._redis.hgetall(_STATUS_CODES_KEY)
        mappings_data = await self._redis.hgetall(_MAPPINGS_KEY)

        total_requests = int(global_data.get("total_requests", 0))
        total_errors = int(global_data.get("total_errors", 0))
        latency_sum = float(global_data.get("latency_sum", 0.0))
        latency_count = int(global_data.get("latency_count", 0))
        avg_latency = round(
            latency_sum / latency_count if latency_count > 0 else 0.0, 2
        )

        by_image = await self._collect_image_metrics()
        by_app_hostname = await self._collect_hostname_metrics()

        result: Dict[str, Any] = {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "avg_latency_ms": avg_latency,
            "status_codes": {k: int(v) for k, v in status_codes_data.items()},
        }

        if by_image:
            result["by_image"] = by_image
        if by_app_hostname:
            result["by_app_hostname"] = by_app_hostname
        if mappings_data:
            result["active_mappings"] = {k: int(v) for k, v in mappings_data.items()}

        return result

    async def get_active_mappings(self) -> Dict[str, int]:
        """Get all active hostname → port mappings."""
        data = await self._redis.hgetall(_MAPPINGS_KEY)
        return {k: int(v) for k, v in data.items()}

    async def reset(self) -> None:
        """Reset all metrics counters by removing all lb:metrics:* keys."""
        keys_to_delete: List[str] = [
            k async for k in self._redis.scan_iter("lb:metrics:*")
        ]
        if keys_to_delete:
            await self._redis.delete(*keys_to_delete)

    async def _collect_image_metrics(self) -> Dict[str, Any]:
        by_image: Dict[str, Any] = {}
        async for key in self._redis.scan_iter("lb:metrics:image:*"):
            if ":status_codes" in key:
                continue
            image_id = key.split(":")[-1]
            data = await self._redis.hgetall(key)
            lat_sum = float(data.get("latency_sum", 0.0))
            lat_count = int(data.get("latency_count", 0))
            by_image[image_id] = {
                "requests": int(data.get("requests", 0)),
                "errors": int(data.get("errors", 0)),
                "avg_latency_ms": round(
                    lat_sum / lat_count if lat_count > 0 else 0.0, 2
                ),
            }
        return by_image

    async def _collect_hostname_metrics(self) -> Dict[str, Any]:
        prefix = "lb:metrics:hostname:"
        by_hostname: Dict[str, Any] = {}
        async for key in self._redis.scan_iter(f"{prefix}*"):
            if ":status_codes" in key:
                continue
            hostname = key[len(prefix) :]
            data = await self._redis.hgetall(key)
            lat_sum = float(data.get("latency_sum", 0.0))
            lat_count = int(data.get("latency_count", 0))
            by_hostname[hostname] = {
                "requests": int(data.get("requests", 0)),
                "errors": int(data.get("errors", 0)),
                "traffic_bytes": int(data.get("traffic", 0)),
                "avg_latency_ms": round(
                    lat_sum / lat_count if lat_count > 0 else 0.0, 2
                ),
            }
        return by_hostname
