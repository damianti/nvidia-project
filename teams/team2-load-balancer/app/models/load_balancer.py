from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

class LoadBalancingAlgorithm(str, Enum):
    """Available load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"

class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceType(str, Enum):
    """Type of service for routing"""
    ORCHESTRATOR = "orchestrator"  # Team 3 - Container management
    BILLING = "billing"           # Team 6 - User management & billing
    USER_CONTAINER = "user_container"  # User's deployed containers

class ContainerInfo(BaseModel):
    """Information about a container instance"""
    container_id: str
    name: str
    port: int
    image_id: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    last_health_check: Optional[datetime] = None
    active_connections: int = 0

class ServiceInfo(BaseModel):
    """Information about a service (image)"""
    image_id: int
    image_name: str
    containers: List[ContainerInfo] = []
    algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN
    total_requests: int = 0
    requests_per_second: float = 0.0
    last_updated: Optional[datetime] = None

class SystemServiceInfo(BaseModel):
    """Information about system services (orchestrator, billing)"""
    service_type: ServiceType
    name: str
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    total_requests: int = 0

class LoadBalancerConfig(BaseModel):
    """Configuration for the load balancer"""
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    max_retries: int = Field(default=3, description="Maximum retries for failed requests")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    default_algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN

class PortMapping(BaseModel):
    """Port mapping information"""
    external_port: int
    image_id: int
    image_name: str
    container_count: int
    total_requests: int = 0

class RoutingRule(BaseModel):
    """Routing rule for different request types"""
    path_pattern: str  # e.g., "/auth/*", "/users/*", "/billing/*"
    service_type: ServiceType
    priority: int = 0  # Higher priority rules are checked first
