import redis
import json
import logging
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from ..database.config import get_db
from ..database.models import Image, Container, User
from .message_queue import MessageQueue, Message, MessageType, MessageStatus

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Message processor for handling asynchronous messages from load balancer"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 1):
        self.message_queue = MessageQueue(redis_host, redis_port, redis_db)
        self.service_id = f"orchestrator-{int(time.time())}"
        self.running = False
        self.worker_thread = None
        
    def start(self):
        """Start the message processor worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info(f"Message processor started: {self.service_id}")
    
    def stop(self):
        """Stop the message processor"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Message processor stopped")
    
    def _worker_loop(self):
        """Main worker loop for processing messages"""
        while self.running:
            try:
                # Receive message with timeout
                message = self.message_queue.receive_message(self.service_id, timeout=1)
                
                if message:
                    logger.info(f"Processing message: {message.message_id} ({message.message_type})")
                    
                    # Update message status to processing
                    self.message_queue.update_message_status(message.message_id, MessageStatus.PROCESSING.value)
                    
                    # Process message based on type
                    success = self._process_message(message)
                    
                    # Update message status
                    if success:
                        self.message_queue.update_message_status(message.message_id, MessageStatus.COMPLETED.value)
                    else:
                        self.message_queue.update_message_status(message.message_id, MessageStatus.FAILED.value, "Processing failed")
                
            except Exception as e:
                logger.error(f"Error in message worker loop: {e}")
                time.sleep(1)  # Brief pause on error
    
    def _process_message(self, message: Message) -> bool:
        """Process a specific message based on its type"""
        try:
            if message.message_type == MessageType.CONTAINER_CREATE.value:
                return self._handle_container_create(message)
            elif message.message_type == MessageType.CONTAINER_START.value:
                return self._handle_container_start(message)
            elif message.message_type == MessageType.CONTAINER_STOP.value:
                return self._handle_container_stop(message)
            elif message.message_type == MessageType.CONTAINER_DELETE.value:
                return self._handle_container_delete(message)
            elif message.message_type == MessageType.IMAGE_PULL.value:
                return self._handle_image_pull(message)
            elif message.message_type == MessageType.HEALTH_CHECK.value:
                return self._handle_health_check(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            return False
    
    def _handle_container_create(self, message: Message) -> bool:
        """Handle container creation request"""
        try:
            payload = message.payload
            image_name = payload.get("image_name")
            tag = payload.get("tag", "latest")
            min_instances = payload.get("min_instances", 1)
            max_instances = payload.get("max_instances", 3)
            
            if not image_name:
                logger.error("Missing image_name in container create message")
                return False
            
            # Get database session
            db = next(get_db())
            
            # Check if image exists, if not pull it
            image = db.query(Image).filter(Image.name == image_name, Image.tag == tag).first()
            if not image:
                # Create image record
                image = Image(
                    name=image_name,
                    tag=tag,
                    min_instances=min_instances,
                    max_instances=max_instances,
                    cpu_limit=payload.get("cpu_limit", "0.5"),
                    memory_limit=payload.get("memory_limit", "512m"),
                    user_id=1  # Default user for now
                )
                db.add(image)
                db.commit()
                db.refresh(image)
            
            # Create containers
            containers_created = []
            for i in range(min_instances):
                try:
                    from ..api.containers import create_container_instance
                    container = create_container_instance(db, image, i)
                    containers_created.append(container)
                except Exception as e:
                    logger.error(f"Failed to create container {i}: {e}")
            
            # Send response
            response_data = {
                "success": True,
                "image_id": image.id,
                "containers_created": len(containers_created),
                "container_ids": [c.id for c in containers_created]
            }
            
            self.message_queue.send_response(message.message_id, response_data)
            logger.info(f"Container creation completed: {len(containers_created)} containers created")
            return True
            
        except Exception as e:
            logger.error(f"Error in container creation: {e}")
            return False
    
    def _handle_container_start(self, message: Message) -> bool:
        """Handle container start request"""
        try:
            payload = message.payload
            container_id = payload.get("container_id")
            
            if not container_id:
                logger.error("Missing container_id in container start message")
                return False
            
            # Get database session
            db = next(get_db())
            
            # Find container
            container = db.query(Container).filter(Container.id == container_id).first()
            if not container:
                logger.error(f"Container not found: {container_id}")
                return False
            
            # Start container using Docker
            import docker
            docker_client = docker.from_env()
            
            try:
                docker_container = docker_client.containers.get(container.container_id)
                docker_container.start()
                container.status = "running"
                db.commit()
                
                response_data = {
                    "success": True,
                    "container_id": container_id,
                    "status": "running"
                }
                
                self.message_queue.send_response(message.message_id, response_data)
                logger.info(f"Container started: {container_id}")
                return True
                
            except docker.errors.NotFound:
                logger.error(f"Docker container not found: {container.container_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in container start: {e}")
            return False
    
    def _handle_container_stop(self, message: Message) -> bool:
        """Handle container stop request"""
        try:
            payload = message.payload
            container_id = payload.get("container_id")
            
            if not container_id:
                logger.error("Missing container_id in container stop message")
                return False
            
            # Get database session
            db = next(get_db())
            
            # Find container
            container = db.query(Container).filter(Container.id == container_id).first()
            if not container:
                logger.error(f"Container not found: {container_id}")
                return False
            
            # Stop container using Docker
            import docker
            docker_client = docker.from_env()
            
            try:
                docker_container = docker_client.containers.get(container.container_id)
                docker_container.stop()
                container.status = "stopped"
                db.commit()
                
                response_data = {
                    "success": True,
                    "container_id": container_id,
                    "status": "stopped"
                }
                
                self.message_queue.send_response(message.message_id, response_data)
                logger.info(f"Container stopped: {container_id}")
                return True
                
            except docker.errors.NotFound:
                logger.error(f"Docker container not found: {container.container_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in container stop: {e}")
            return False
    
    def _handle_container_delete(self, message: Message) -> bool:
        """Handle container delete request"""
        try:
            payload = message.payload
            container_id = payload.get("container_id")
            
            if not container_id:
                logger.error("Missing container_id in container delete message")
                return False
            
            # Get database session
            db = next(get_db())
            
            # Find container
            container = db.query(Container).filter(Container.id == container_id).first()
            if not container:
                logger.error(f"Container not found: {container_id}")
                return False
            
            # Delete container using Docker
            import docker
            docker_client = docker.from_env()
            
            try:
                docker_container = docker_client.containers.get(container.container_id)
                docker_container.remove(force=True)
                
                # Delete from database
                db.delete(container)
                db.commit()
                
                response_data = {
                    "success": True,
                    "container_id": container_id,
                    "message": "Container deleted"
                }
                
                self.message_queue.send_response(message.message_id, response_data)
                logger.info(f"Container deleted: {container_id}")
                return True
                
            except docker.errors.NotFound:
                # Container already deleted, just remove from database
                db.delete(container)
                db.commit()
                
                response_data = {
                    "success": True,
                    "container_id": container_id,
                    "message": "Container already deleted"
                }
                
                self.message_queue.send_response(message.message_id, response_data)
                return True
                
        except Exception as e:
            logger.error(f"Error in container delete: {e}")
            return False
    
    def _handle_image_pull(self, message: Message) -> bool:
        """Handle image pull request"""
        try:
            payload = message.payload
            image_name = payload.get("image_name")
            tag = payload.get("tag", "latest")
            
            if not image_name:
                logger.error("Missing image_name in image pull message")
                return False
            
            # Pull image using Docker
            import docker
            docker_client = docker.from_env()
            
            try:
                docker_client.images.pull(f"{image_name}:{tag}")
                
                response_data = {
                    "success": True,
                    "image_name": image_name,
                    "tag": tag,
                    "message": "Image pulled successfully"
                }
                
                self.message_queue.send_response(message.message_id, response_data)
                logger.info(f"Image pulled: {image_name}:{tag}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to pull image {image_name}:{tag}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error in image pull: {e}")
            return False
    
    def _handle_health_check(self, message: Message) -> bool:
        """Handle health check request"""
        try:
            response_data = {
                "success": True,
                "service_id": self.service_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "healthy"
            }
            
            self.message_queue.send_response(message.message_id, response_data)
            logger.info("Health check response sent")
            return True
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return False
