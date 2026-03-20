"""
Round Robin Service Selector for Load Balancer.

Uses Redis INCR for atomic, distributed round-robin index management.
"""

from typing import List, Optional

import redis.asyncio as aioredis

from app.schemas.service_info import ServiceInfo


class RoundRobinSelector:
    """
    Maintains a round-robin index per image_id in Redis.

    Redis INCR is atomic, so no locking is needed even with multiple instances.
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def select(
        self, image_id: int, services: List[ServiceInfo]
    ) -> Optional[ServiceInfo]:
        """
        Select the next service using round-robin algorithm.

        Args:
            image_id: ID of the image to select a service for
            services: List of available healthy services for this image

        Returns:
            Selected ServiceInfo, or None if services list is empty
        """
        if not services:
            return None

        index = await self._redis.incr(f"lb:rr:index:{image_id}")
        return services[(index - 1) % len(services)]
