import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from app.utils.config import SERVICE_NAME
from app.schemas.service_info import ServiceInfo
from app.services.website_mapping import AppHostnameMapping

logger = logging.getLogger(SERVICE_NAME)


class ServiceCache:
    """
    In-memory cache of healthy services from Consul.
    Automatically updated via Watch API.
    """
    
    def __init__(self, app_hostname_map: Optional[AppHostnameMapping] = None):
        self._cache: Dict[int, List[ServiceInfo]] = {}
        self._app_hostname_map = app_hostname_map or AppHostnameMapping()
        self._lock = asyncio.Lock()
        self._last_index: int = 0
        self._last_update: Optional[datetime] = None
    
    async def update_services(self, services: List[ServiceInfo], index: int) -> None:
        """
        Updates cache with new services from Consul.
        
        Args:
            services: List of healthy services from Consul
            index: Last Consul index (for long polling)
        """
        async with self._lock:
            
            self._cache.clear()
            self._app_hostname_map.clear()

            for service in services:
                if service.image_id is None:
                    continue
                
                if service.image_id not in self._cache:
                    self._cache[service.image_id] = []
                
                self._cache[service.image_id].append(service)
                if service.app_hostname:
                    self._app_hostname_map.add(service.app_hostname, service.image_id)
            
            self._last_index = index
            self._last_update = datetime.now()
            
            logger.info(
                "cache.updated",
                extra={
                    "services_count": len(services),
                    "image_ids": list(self._cache.keys()),
                    "index": index
                }
            )
    
    def get_services(
        self,
        *,
        image_id: Optional[int] = None,
        app_hostname: Optional[str] = None,
    ) -> List[ServiceInfo]:
        """
        Gets services from cache.
        
        Args:
            image_id: Filter by image identifier
            app_hostname: Filter by app hostname
        
        Returns:
            List of services
        """
        if app_hostname:
            image_id = self._app_hostname_map.get_image_id(app_hostname)
            if image_id is None:
                return []

        if image_id is not None:
            return self._cache.get(image_id, [])

        services: List[ServiceInfo] = []
        for service_list in self._cache.values():
            services.extend(service_list)
        return services
    
    def get_cache_status(self) -> Dict:
        """Returns cache status (for debugging)"""
        return {
            "last_index": self._last_index,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "image_ids": list(self._cache.keys()),
            "total_services": sum(len(services) for services in self._cache.values()),
            "app_hostname_mappings": self._app_hostname_map.size(),
        }