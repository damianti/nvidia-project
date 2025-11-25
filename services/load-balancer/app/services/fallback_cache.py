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
        # Key: website_url (normalized), Value: (services, timestamp)
        self._cache: Dict[str, tuple[List[ServiceInfo], datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def update(self, website_url: str, services: List[ServiceInfo]) -> None:
        """
        Update cache with new services for a website_url.
        """
        async with self._lock:
            normalized_url = self._normalize_url(website_url)
            self._cache[normalized_url] = (services, datetime.now())
            logger.debug(
                "fallback_cache.updated",
                extra={
                    "website_url": normalized_url,
                    "services_count": len(services)
                }
            )
    
    async def get(self, website_url: str) -> Optional[List[ServiceInfo]]:
        """
        Get cached services for website_url if not expired.
        
        Returns:
            List of ServiceInfo if found and not expired, None otherwise
        """
        async with self._lock:
            normalized_url = self._normalize_url(website_url)
            
            logger.info(
                "fallback_cache.get_attempt",
                extra={
                    "website_url": website_url,
                    "normalized_url": normalized_url,
                    "cache_keys": list(self._cache.keys())
                }
            )
            
            if normalized_url not in self._cache:
                logger.warning(
                    "fallback_cache.key_not_found",
                    extra={
                        "normalized_url": normalized_url,
                        "available_keys": list(self._cache.keys())
                    }
                )
                return None
            
            services, timestamp = self._cache[normalized_url]
            elapsed = (datetime.now() - timestamp).total_seconds()
            
            if elapsed > self.ttl_seconds:
                # Expired, remove from cache
                del self._cache[normalized_url]
                logger.debug(
                    "fallback_cache.expired",
                    extra={
                        "website_url": normalized_url,
                        "elapsed_seconds": elapsed
                    }
                )
                return None
            
            logger.debug(
                "fallback_cache.hit",
                extra={
                    "website_url": normalized_url,
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
    
    def _normalize_url(self, website_url: str) -> str:
        """Normalize website URL for consistent cache keys"""
        if not website_url:
            return ""
        normalized = website_url.strip().lower()
        # Remove protocol
        if normalized.startswith("https://"):
            normalized = normalized[8:]
        elif normalized.startswith("http://"):
            normalized = normalized[7:]
        # Remove trailing slash
        normalized = normalized.rstrip("/")
        return normalized
    
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

