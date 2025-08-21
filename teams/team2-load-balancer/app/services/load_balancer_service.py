import httpx
import asyncio
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.models.load_balancer import (
    ServiceInfo, 
    ContainerInfo, 
    ServiceStatus, 
    LoadBalancingAlgorithm,
    PortMapping,
    ServiceType,
    SystemServiceInfo,
    RoutingRule
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancerService:
    """Core load balancer service that manages request distribution"""
    
    def __init__(self):
        # Store services by image_id (user containers)
        self.services: Dict[int, ServiceInfo] = {}
        # Store system services (orchestrator, billing)
        self.system_services: Dict[ServiceType, SystemServiceInfo] = {}
        # Store port mappings
        self.port_mappings: Dict[int, PortMapping] = {}
        # Round-robin counters for each service
        self.round_robin_counters: Dict[int, int] = {}
        # HTTP client for forwarding requests
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize default routing rules
        self.routing_rules = [
            RoutingRule(path_pattern="/auth/*", service_type=ServiceType.ORCHESTRATOR, priority=10),
            RoutingRule(path_pattern="/users/*", service_type=ServiceType.BILLING, priority=10),
            RoutingRule(path_pattern="/billing/*", service_type=ServiceType.BILLING, priority=10),
            RoutingRule(path_pattern="/images/*", service_type=ServiceType.ORCHESTRATOR, priority=10),
            RoutingRule(path_pattern="/containers/*", service_type=ServiceType.ORCHESTRATOR, priority=10),
        ]
        
        # Initialize default system services
        self.system_services[ServiceType.ORCHESTRATOR] = SystemServiceInfo(
            service_type=ServiceType.ORCHESTRATOR,
            name="orchestrator",
            host="localhost",
            port=3003
        )
        self.system_services[ServiceType.BILLING] = SystemServiceInfo(
            service_type=ServiceType.BILLING,
            name="billing",
            host="localhost", 
            port=8000
        )
        
    def determine_service_type(self, path: str) -> Tuple[ServiceType, Optional[int]]:
        """
        Determine which service should handle the request based on path
        Returns: (service_type, image_id) where image_id is None for system services
        """
        # Sort rules by priority (highest first)
        sorted_rules = sorted(self.routing_rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            # Convert pattern to regex (e.g., "/auth/*" -> "^/auth/")
            pattern = rule.path_pattern.replace("*", ".*")
            if re.match(pattern, path):
                return rule.service_type, None
        
        # If no rule matches, check if it's a user container request
        # Format: /proxy/{image_id}/{path}
        proxy_match = re.match(r"^/proxy/(\d+)/(.*)$", path)
        if proxy_match:
            image_id = int(proxy_match.group(1))
            return ServiceType.USER_CONTAINER, image_id
            
        # Default to orchestrator for unknown paths
        return ServiceType.ORCHESTRATOR, None
        
    async def register_service(self, image_id: int, image_name: str, containers: List[ContainerInfo]) -> None:
        """Register a new service or update existing service with containers"""
        logger.info(f"Registering service: {image_name} (ID: {image_id}) with {len(containers)} containers")
        
        # Create or update service
        if image_id not in self.services:
            self.services[image_id] = ServiceInfo(
                image_id=image_id,
                image_name=image_name,
                containers=containers
            )
            self.round_robin_counters[image_id] = 0
        else:
            # Update existing service
            self.services[image_id].containers = containers
            self.services[image_id].last_updated = datetime.now()
            
        # Update port mappings
        for container in containers:
            if container.port not in self.port_mappings:
                self.port_mappings[container.port] = PortMapping(
                    external_port=container.port,
                    image_id=image_id,
                    image_name=image_name,
                    container_count=len(containers)
                )
    
    def get_next_container_round_robin(self, image_id: int) -> Optional[ContainerInfo]:
        """Get next container using round-robin algorithm"""
        if image_id not in self.services:
            return None
            
        service = self.services[image_id]
        if not service.containers:
            return None
            
        # Get healthy containers only
        healthy_containers = [c for c in service.containers if c.status == ServiceStatus.HEALTHY]
        if not healthy_containers:
            logger.warning(f"No healthy containers for image {image_id}")
            return None
            
        # Round-robin selection
        counter = self.round_robin_counters[image_id]
        selected_container = healthy_containers[counter % len(healthy_containers)]
        self.round_robin_counters[image_id] = (counter + 1) % len(healthy_containers)
        
        return selected_container
    
    def get_least_connections_container(self, image_id: int) -> Optional[ContainerInfo]:
        """Get container with least active connections"""
        if image_id not in self.services:
            return None
            
        service = self.services[image_id]
        healthy_containers = [c for c in service.containers if c.status == ServiceStatus.HEALTHY]
        
        if not healthy_containers:
            return None
            
        # Find container with minimum active connections
        return min(healthy_containers, key=lambda c: c.active_connections)
    
    def select_container(self, image_id: int, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN) -> Optional[ContainerInfo]:
        """Select container based on the specified algorithm"""
        if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self.get_next_container_round_robin(image_id)
        elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self.get_least_connections_container(image_id)
        else:
            # Default to round-robin
            return self.get_next_container_round_robin(image_id)
    
    async def forward_request(self, path: str, method: str, headers: Dict, body: Optional[bytes] = None) -> httpx.Response:
        """Forward request to appropriate service based on path"""
        service_type, image_id = self.determine_service_type(path)
        
        if service_type == ServiceType.USER_CONTAINER:
            return await self._forward_to_user_container(image_id, path, method, headers, body)
        else:
            return await self._forward_to_system_service(service_type, path, method, headers, body)
    
    async def _forward_to_user_container(self, image_id: int, path: str, method: str, headers: Dict, body: Optional[bytes] = None) -> httpx.Response:
        """Forward request to user container"""
        # Select container based on algorithm
        service = self.services.get(image_id)
        if not service:
            raise ValueError(f"Service not found for image_id: {image_id}")
            
        container = self.select_container(image_id, service.algorithm)
        if not container:
            raise ValueError(f"No healthy containers available for image_id: {image_id}")
        
        # Increment active connections
        container.active_connections += 1
        service.total_requests += 1
        
        try:
            # Extract the actual path from /proxy/{image_id}/{path}
            actual_path = re.sub(r"^/proxy/\d+/", "/", path)
            
            # Build target URL
            target_url = f"http://localhost:{container.port}{actual_path}"
            logger.info(f"Forwarding {method} request to user container: {target_url}")
            
            # Forward the request
            response = await self.http_client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error forwarding request to user container: {e}")
            # Mark container as unhealthy on error
            container.status = ServiceStatus.UNHEALTHY
            raise
        finally:
            # Decrement active connections
            container.active_connections = max(0, container.active_connections - 1)
    
    async def _forward_to_system_service(self, service_type: ServiceType, path: str, method: str, headers: Dict, body: Optional[bytes] = None) -> httpx.Response:
        """Forward request to system service (orchestrator or billing)"""
        system_service = self.system_services.get(service_type)
        if not system_service:
            raise ValueError(f"System service not found: {service_type}")
        
        # Increment request counter
        system_service.total_requests += 1
        
        try:
            # Build target URL
            target_url = f"http://{system_service.host}:{system_service.port}{path}"
            logger.info(f"Forwarding {method} request to {service_type.value}: {target_url}")
            
            # Forward the request
            response = await self.http_client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error forwarding request to {service_type.value}: {e}")
            # Mark service as unhealthy on error
            system_service.status = ServiceStatus.UNHEALTHY
            raise
    
    def get_service_info(self, image_id: int) -> Optional[ServiceInfo]:
        """Get information about a specific service"""
        return self.services.get(image_id)
    
    def get_all_services(self) -> List[ServiceInfo]:
        """Get all registered services"""
        return list(self.services.values())
    
    def get_system_services(self) -> List[SystemServiceInfo]:
        """Get all system services"""
        return list(self.system_services.values())
    
    def get_port_mappings(self) -> List[PortMapping]:
        """Get all port mappings"""
        return list(self.port_mappings.values())
    
    async def health_check_container(self, container: ContainerInfo) -> bool:
        """Perform health check on a container"""
        try:
            response = await self.http_client.get(f"http://localhost:{container.port}/health", timeout=5.0)
            is_healthy = response.status_code == 200
            container.status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            container.last_health_check = datetime.now()
            return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for container {container.name}: {e}")
            container.status = ServiceStatus.UNHEALTHY
            container.last_health_check = datetime.now()
            return False
    
    async def health_check_system_service(self, service_type: ServiceType) -> bool:
        """Perform health check on a system service"""
        system_service = self.system_services.get(service_type)
        if not system_service:
            return False
            
        try:
            response = await self.http_client.get(f"http://{system_service.host}:{system_service.port}/health", timeout=5.0)
            is_healthy = response.status_code == 200
            system_service.status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            system_service.last_health_check = datetime.now()
            return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for {service_type.value}: {e}")
            system_service.status = ServiceStatus.UNHEALTHY
            system_service.last_health_check = datetime.now()
            return False
    
    async def perform_health_checks(self) -> None:
        """Perform health checks on all containers and system services"""
        logger.info("Performing health checks on all services")
        
        # Check user containers
        for service in self.services.values():
            for container in service.containers:
                await self.health_check_container(container)
        
        # Check system services
        for service_type in [ServiceType.ORCHESTRATOR, ServiceType.BILLING]:
            await self.health_check_system_service(service_type)
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.http_client.aclose()

# Global instance
load_balancer_service = LoadBalancerService()
