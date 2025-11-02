import redis
import json
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger("orchestrator")

@dataclass
class ServiceInfo:
    """Service information for registration"""
    service_id: str
    service_type: str
    host: str
    port: int
    health_endpoint: str
    status: str = "healthy"
    last_heartbeat: Optional[str] = None
    metadata: Optional[Dict] = None

class ServiceDiscovery:
    """Service Discovery using Redis as backend"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=redis_db, 
            decode_responses=True
        )
        self.service_prefix = "service:"
        self.heartbeat_prefix = "heartbeat:"
        self.heartbeat_ttl = 30  # seconds
        
    def register_service(self, service: ServiceInfo) -> bool:
        """Register a service in the discovery system"""
        try:
            service_key = f"{self.service_prefix}{service.service_type}:{service.service_id}"
            service_data = asdict(service)
            service_data['registered_at'] = datetime.utcnow().isoformat()
            
            # Store service info
            self.redis_client.hset(service_key, mapping=service_data)
            
            # Add to service type index
            self.redis_client.sadd(f"services:{service.service_type}", service.service_id)
            
            # Set heartbeat
            self._update_heartbeat(service.service_id)
            
            logger.info(f"Service registered: {service.service_type}:{service.service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            return False
    
    def deregister_service(self, service_type: str, service_id: str) -> bool:
        """Deregister a service from the discovery system"""
        try:
            service_key = f"{self.service_prefix}{service_type}:{service_id}"
            
            # Remove service info
            self.redis_client.delete(service_key)
            
            # Remove from service type index
            self.redis_client.srem(f"services:{service_type}", service_id)
            
            # Remove heartbeat
            self.redis_client.delete(f"{self.heartbeat_prefix}{service_id}")
            
            logger.info(f"Service deregistered: {service_type}:{service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            return False
    
    def get_services(self, service_type: str) -> List[ServiceInfo]:
        """Get all services of a specific type"""
        try:
            service_ids = self.redis_client.smembers(f"services:{service_type}")
            services = []
            
            for service_id in service_ids:
                service_key = f"{self.service_prefix}{service_type}:{service_id}"
                service_data = self.redis_client.hgetall(service_key)
                
                if service_data and self._is_service_healthy(service_id):
                    service = ServiceInfo(
                        service_id=service_data.get('service_id'),
                        service_type=service_data.get('service_type'),
                        host=service_data.get('host'),
                        port=int(service_data.get('port', 0)),
                        health_endpoint=service_data.get('health_endpoint'),
                        status=service_data.get('status', 'healthy'),
                        last_heartbeat=service_data.get('last_heartbeat'),
                        metadata=json.loads(service_data.get('metadata', '{}'))
                    )
                    services.append(service)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []
    
    def get_service(self, service_type: str, service_id: str) -> Optional[ServiceInfo]:
        """Get a specific service by type and ID"""
        try:
            service_key = f"{self.service_prefix}{service_type}:{service_id}"
            service_data = self.redis_client.hgetall(service_key)
            
            if service_data and self._is_service_healthy(service_id):
                return ServiceInfo(
                    service_id=service_data.get('service_id'),
                    service_type=service_data.get('service_type'),
                    host=service_data.get('host'),
                    port=int(service_data.get('port', 0)),
                    health_endpoint=service_data.get('health_endpoint'),
                    status=service_data.get('status', 'healthy'),
                    last_heartbeat=service_data.get('last_heartbeat'),
                    metadata=json.loads(service_data.get('metadata', '{}'))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get service: {e}")
            return None
    
    def update_heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat"""
        try:
            self._update_heartbeat(service_id)
            return True
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
            return False
    
    def _update_heartbeat(self, service_id: str):
        """Internal method to update heartbeat"""
        heartbeat_key = f"{self.heartbeat_prefix}{service_id}"
        self.redis_client.setex(heartbeat_key, self.heartbeat_ttl, datetime.utcnow().isoformat())
        
        # Update last_heartbeat in service info
        for key in self.redis_client.scan_iter(f"{self.service_prefix}*"):
            if service_id in key:
                self.redis_client.hset(key, 'last_heartbeat', datetime.utcnow().isoformat())
                break
    
    def _is_service_healthy(self, service_id: str) -> bool:
        """Check if service is healthy based on heartbeat"""
        try:
            heartbeat_key = f"{self.heartbeat_prefix}{service_id}"
            return self.redis_client.exists(heartbeat_key) > 0
        except Exception:
            return False
    
    def cleanup_dead_services(self) -> int:
        """Clean up services that haven't sent heartbeat"""
        try:
            cleaned_count = 0
            
            for key in self.redis_client.scan_iter(f"{self.service_prefix}*"):
                service_data = self.redis_client.hgetall(key)
                service_id = service_data.get('service_id')
                
                if service_id and not self._is_service_healthy(service_id):
                    service_type = service_data.get('service_type')
                    if self.deregister_service(service_type, service_id):
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} dead services")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup dead services: {e}")
            return 0
