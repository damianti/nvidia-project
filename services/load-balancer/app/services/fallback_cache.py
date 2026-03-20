"""
Fallback Cache for Load Balancer.

Stores the last known healthy services per app_hostname in Redis with automatic
TTL expiration. Used when Service Discovery is unavailable.
"""

import json
import logging
from typing import List, Optional

import redis.asyncio as aioredis

from app.schemas.service_info import ServiceInfo
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

_KEY_PREFIX = "lb:fallback:"


class FallbackCache:
    """
    Cache for storing last known healthy services, backed by Redis.

    TTL is enforced natively by Redis — no manual expiration logic needed.
    """

    def __init__(self, redis: aioredis.Redis, ttl_seconds: float = 10.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._redis = redis

    async def update(self, app_hostname: str, services: List[ServiceInfo]) -> None:
        """Update cache with new services for an app_hostname."""
        normalized = self._normalize_hostname(app_hostname)
        key = f"{_KEY_PREFIX}{normalized}"
        value = json.dumps([s.model_dump() for s in services])
        await self._redis.set(key, value, ex=int(self.ttl_seconds))
        logger.debug(
            "fallback_cache.updated",
            extra={"app_hostname": normalized, "services_count": len(services)},
        )

    async def get(self, app_hostname: str) -> Optional[List[ServiceInfo]]:
        """
        Get cached services for app_hostname.

        Returns None if not found or TTL has expired (Redis handles expiry).
        """
        normalized = self._normalize_hostname(app_hostname)
        key = f"{_KEY_PREFIX}{normalized}"

        logger.info(
            "fallback_cache.get_attempt",
            extra={"app_hostname": app_hostname, "normalized_hostname": normalized},
        )

        data = await self._redis.get(key)
        if data is None:
            logger.warning(
                "fallback_cache.key_not_found",
                extra={"normalized_hostname": normalized},
            )
            return None

        services = [ServiceInfo(**s) for s in json.loads(data)]
        logger.debug(
            "fallback_cache.hit",
            extra={"app_hostname": normalized, "services_count": len(services)},
        )
        return services

    async def clear(self) -> None:
        """Clear all fallback cache entries."""
        keys_to_delete: List[str] = [
            k async for k in self._redis.scan_iter(f"{_KEY_PREFIX}*")
        ]
        if keys_to_delete:
            await self._redis.delete(*keys_to_delete)
        logger.debug("fallback_cache.cleared")

    def _normalize_hostname(self, app_hostname: str) -> str:
        """Normalize app hostname for consistent cache keys."""
        if not app_hostname:
            return ""
        normalized = app_hostname.strip().lower()

        if normalized.startswith("https://"):
            normalized = normalized[8:]
        elif normalized.startswith("http://"):
            normalized = normalized[7:]

        for sep in ("/", "?", "#"):
            normalized = normalized.split(sep, 1)[0]

        if normalized.count(":") == 1:
            host, port = normalized.rsplit(":", 1)
            if port.isdigit():
                normalized = host

        return normalized.rstrip("/")

    async def get_status(self) -> dict:
        """Get cache status for debugging."""
        keys: List[str] = [k async for k in self._redis.scan_iter(f"{_KEY_PREFIX}*")]
        return {
            "entries_count": len(keys),
            "ttl_seconds": self.ttl_seconds,
        }
