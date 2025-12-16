import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.schemas.service_info import ServiceInfo
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class FallbackCache:
    """
    Cache for storing last known healthy services.
    
    Used as fallback when Service Discovery is unavailable.
    Cache entries expire after TTL seconds.
    """
    
    def __init__(self, ttl_seconds: float = 10.0) -> None:
        """
        Args:
            ttl_seconds: Time to live for cache entries (default: 10s)
        """
        self.ttl_seconds = ttl_seconds
        # Key: app_hostname (normalized), Value: (services, timestamp)
        self._cache: Dict[str, tuple[List[ServiceInfo], datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def update(self, app_hostname: str, services: List[ServiceInfo]) -> None:
        """
        Update cache with new services for an app_hostname.
        """
        async with self._lock:
            normalized_hostname = self._normalize_hostname(app_hostname)
            self._cache[normalized_hostname] = (services, datetime.now())
            logger.debug(
                "fallback_cache.updated",
                extra={
                    "app_hostname": normalized_hostname,
                    "services_count": len(services)
                }
            )
    
    async def get(self, app_hostname: str) -> Optional[List[ServiceInfo]]:
        """
        Get cached services for app_hostname if not expired.
        
        Returns:
            List of ServiceInfo if found and not expired, None otherwise
        """
        async with self._lock:
            normalized_hostname = self._normalize_hostname(app_hostname)
            
            logger.info(
                "fallback_cache.get_attempt",
                extra={
                    "app_hostname": app_hostname,
                    "normalized_hostname": normalized_hostname,
                    "cache_keys": list(self._cache.keys())
                }
            )
            
            if normalized_hostname not in self._cache:
                logger.warning(
                    "fallback_cache.key_not_found",
                    extra={
                        "normalized_hostname": normalized_hostname,
                        "available_keys": list(self._cache.keys())
                    }
                )
                return None
            
            services, timestamp = self._cache[normalized_hostname]
            elapsed = (datetime.now() - timestamp).total_seconds()
            
            if elapsed > self.ttl_seconds:
                # Expired, remove from cache
                del self._cache[normalized_hostname]
                logger.debug(
                    "fallback_cache.expired",
                    extra={
                        "app_hostname": normalized_hostname,
                        "elapsed_seconds": elapsed
                    }
                )
                return None
            
            logger.debug(
                "fallback_cache.hit",
                extra={
                    "app_hostname": normalized_hostname,
                    "services_count": len(services),
                    "age_seconds": elapsed
                }
            )
            return services
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            logger.debug("fallback_cache.cleared")
    
    def _normalize_hostname(self, app_hostname: str) -> str:
        """Normalize app hostname for consistent cache keys"""
        if not app_hostname:
            return ""
        return app_hostname.strip().lower()
    
    def get_status(self) -> dict:
        """Get cache status for debugging"""
        return {
            "entries_count": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
            "entries": {
                url: {
                    "services_count": len(services),
                    "age_seconds": (datetime.now() - timestamp).total_seconds()
                }
                for url, (services, timestamp) in self._cache.items()
            }
        }

