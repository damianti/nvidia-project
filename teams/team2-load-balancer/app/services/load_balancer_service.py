import logging
import requests
import time
from typing import Dict, List, Optional
from .service_discovery import ServiceDiscovery, ServiceInfo
from .message_queue import MessageQueue, Message, MessageType, create_container_message, create_container_control_message

logger = logging.getLogger(__name__)

class LoadBalancerService:
    """Enhanced Load Balancer with Service Discovery and Message Queue"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.service_discovery = ServiceDiscovery(redis_host, redis_port, redis_db=0)
        self.message_queue = MessageQueue(redis_host, redis_port, redis_db=1)
        self.service_id = f"load-balancer-{int(time.time())}"
        self.service_type = "load_balancer"
        
        # Register this load balancer instance
        self._register_self()
        
    def _register_self(self):
        """Register this load balancer instance in service discovery"""
        service_info = ServiceInfo(
            service_id=self.service_id,
            service_type=self.service_type,
            host="localhost",  # Will be updated with actual host
            port=3002,  # Load balancer port
            health_endpoint="/health",
            metadata={
                "version": "1.0.0",
                "capabilities": ["container_management", "load_balancing", "service_discovery"]
            }
        )
        
        if self.service_discovery.register_service(service_info):
            logger.info(f"Load balancer registered: {self.service_id}")
        else:
            logger.error("Failed to register load balancer")
    
    def get_orchestrator_service(self) -> Optional[ServiceInfo]:
        """Get orchestrator service from service discovery"""
        orchestrators = self.service_discovery.get_services("orchestrator")
        if orchestrators:
            return orchestrators[0]  # Return first available orchestrator
        return None
    
    def create_container_async(self, image_name: str, tag: str = "latest", 
                             min_instances: int = 1, max_instances: int = 3) -> str:
        """Create container asynchronously via message queue"""
        try:
            orchestrator = self.get_orchestrator_service()
            if not orchestrator:
                raise Exception("No orchestrator service available")
            
            # Create message
            message = create_container_message(
                sender=self.service_id,
                recipient=orchestrator.service_id,
                image_name=image_name,
                tag=tag,
                min_instances=min_instances,
                max_instances=max_instances
            )
            
            # Send message
            if self.message_queue.send_message(message):
                logger.info(f"Container creation request sent: {message.message_id}")
                return message.message_id
            else:
                raise Exception("Failed to send container creation message")
                
        except Exception as e:
            logger.error(f"Failed to create container asynchronously: {e}")
            raise
    
    def start_container_async(self, container_id: str) -> str:
        """Start container asynchronously via message queue"""
        try:
            orchestrator = self.get_orchestrator_service()
            if not orchestrator:
                raise Exception("No orchestrator service available")
            
            # Create message
            message = create_container_control_message(
                sender=self.service_id,
                recipient=orchestrator.service_id,
                message_type=MessageType.CONTAINER_START,
                container_id=container_id
            )
            
            # Send message
            if self.message_queue.send_message(message):
                logger.info(f"Container start request sent: {message.message_id}")
                return message.message_id
            else:
                raise Exception("Failed to send container start message")
                
        except Exception as e:
            logger.error(f"Failed to start container asynchronously: {e}")
            raise
    
    def stop_container_async(self, container_id: str) -> str:
        """Stop container asynchronously via message queue"""
        try:
            orchestrator = self.get_orchestrator_service()
            if not orchestrator:
                raise Exception("No orchestrator service available")
            
            # Create message
            message = create_container_control_message(
                sender=self.service_id,
                recipient=orchestrator.service_id,
                message_type=MessageType.CONTAINER_STOP,
                container_id=container_id
            )
            
            # Send message
            if self.message_queue.send_message(message):
                logger.info(f"Container stop request sent: {message.message_id}")
                return message.message_id
            else:
                raise Exception("Failed to send container stop message")
                
        except Exception as e:
            logger.error(f"Failed to stop container asynchronously: {e}")
            raise
    
    def get_message_status(self, message_id: str) -> Optional[str]:
        """Get status of a message"""
        return self.message_queue.get_message_status(message_id)
    
    def receive_responses(self, timeout: int = 5) -> List[Message]:
        """Receive response messages"""
        responses = []
        while True:
            message = self.message_queue.receive_message(self.service_id, timeout=1)
            if message:
                if message.message_type.startswith("response_"):
                    responses.append(message)
                    logger.info(f"Received response: {message.message_id}")
            else:
                break
        return responses
    
    def route_request(self, service_type: str, path: str, method: str = "GET", 
                     data: Dict = None, headers: Dict = None) -> Dict:
        """Route request to appropriate service using service discovery"""
        try:
            # Get available services
            services = self.service_discovery.get_services(service_type)
            if not services:
                raise Exception(f"No {service_type} services available")
            
            # Simple round-robin selection
            service = services[0]  # For now, just use first available
            
            # Build URL
            url = f"http://{service.host}:{service.port}{path}"
            
            # Make request
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=10
            )
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "service_id": service.service_id
            }
            
        except Exception as e:
            logger.error(f"Failed to route request: {e}")
            raise
    
    def update_heartbeat(self):
        """Update load balancer heartbeat"""
        self.service_discovery.update_heartbeat(self.service_id)
    
    def cleanup_dead_services(self) -> int:
        """Clean up dead services"""
        return self.service_discovery.cleanup_dead_services()
    
    def get_service_stats(self) -> Dict:
        """Get service statistics"""
        try:
            stats = {
                "load_balancer_id": self.service_id,
                "queue_length": self.message_queue.get_queue_length(self.service_id),
                "available_services": {}
            }
            
            # Get stats for each service type
            for service_type in ["orchestrator", "billing", "ui"]:
                services = self.service_discovery.get_services(service_type)
                stats["available_services"][service_type] = len(services)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {}
    
    def deregister_self(self):
        """Deregister this load balancer instance"""
        self.service_discovery.deregister_service(self.service_type, self.service_id)
        logger.info(f"Load balancer deregistered: {self.service_id}")
