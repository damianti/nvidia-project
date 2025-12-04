import redis
import json
import uuid
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestrator")

class MessageType(Enum):
    """Types of messages for different operations"""
    CONTAINER_CREATE = "container_create"
    CONTAINER_START = "container_start"
    CONTAINER_STOP = "container_stop"
    CONTAINER_DELETE = "container_delete"
    IMAGE_PULL = "image_pull"
    HEALTH_CHECK = "health_check"
    SERVICE_REGISTER = "service_register"
    SERVICE_DEREGISTER = "service_deregister"

class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class Message:
    """Message structure for queue communication"""
    message_id: str
    message_type: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    status: str = MessageStatus.PENDING.value
    created_at: Optional[str] = None
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class MessageQueue:
    """Message Queue using Redis for asynchronous communication"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 1):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=redis_db, 
            decode_responses=True
        )
        self.queue_prefix = "queue:"
        self.message_prefix = "message:"
        self.response_prefix = "response:"
        self.timeout = 30  # seconds
        
    def send_message(self, message: Message) -> bool:
        """Send a message to the queue"""
        try:
            # Set creation time
            message.created_at = datetime.utcnow().isoformat()
            
            # Store message
            message_key = f"{self.message_prefix}{message.message_id}"
            message_data = asdict(message)
            self.redis_client.hset(message_key, mapping=message_data)
            
            # Add to recipient's queue
            queue_key = f"{self.queue_prefix}{message.recipient}"
            self.redis_client.lpush(queue_key, message.message_id)
            
            # Set message TTL
            self.redis_client.expire(message_key, self.timeout * 2)
            
            logger.info(
                "message_queue.send.success",
                extra={
                    "message_id": message.message_id,
                    "message_type": message.message_type,
                    "recipient": message.recipient,
                    "sender": message.sender
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                "message_queue.send.failed",
                extra={
                    "message_id": message.message_id,
                    "recipient": message.recipient,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    def receive_message(self, recipient: str, timeout: int = 5) -> Optional[Message]:
        """Receive a message from the queue"""
        try:
            queue_key = f"{self.queue_prefix}{recipient}"
            message_id = self.redis_client.brpop(queue_key, timeout=timeout)
            
            if message_id:
                message_id = message_id[1]  # brpop returns (key, value)
                message_key = f"{self.message_prefix}{message_id}"
                message_data = self.redis_client.hgetall(message_key)
                
                if message_data:
                    return Message(
                        message_id=message_data.get('message_id'),
                        message_type=message_data.get('message_type'),
                        sender=message_data.get('sender'),
                        recipient=message_data.get('recipient'),
                        payload=json.loads(message_data.get('payload', '{}')),
                        status=message_data.get('status'),
                        created_at=message_data.get('created_at'),
                        processed_at=message_data.get('processed_at'),
                        error_message=message_data.get('error_message'),
                        retry_count=int(message_data.get('retry_count', 0)),
                        max_retries=int(message_data.get('max_retries', 3))
                    )
            
            return None
            
        except Exception as e:
            logger.error(
                "message_queue.receive.failed",
                extra={
                    "recipient": recipient,
                    "timeout": timeout,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return None
    
    def update_message_status(self, message_id: str, status: str, error_message: str = None) -> bool:
        """Update message status"""
        try:
            message_key = f"{self.message_prefix}{message_id}"
            
            updates = {
                'status': status,
                'processed_at': datetime.utcnow().isoformat()
            }
            
            if error_message:
                updates['error_message'] = error_message
            
            self.redis_client.hset(message_key, mapping=updates)
            return True
            
        except Exception as e:
            logger.error(
                "message_queue.update_status.failed",
                extra={
                    "message_id": message_id,
                    "status": status,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    def send_response(self, original_message_id: str, response_data: Dict[str, Any]) -> bool:
        """Send a response to an original message"""
        try:
            # Get original message
            original_message_key = f"{self.message_prefix}{original_message_id}"
            original_message_data = self.redis_client.hgetall(original_message_key)
            
            if not original_message_data:
                logger.warning(
                    "message_queue.response.original_not_found",
                    extra={
                        "original_message_id": original_message_id
                    }
                )
                return False
            
            # Create response message
            response_message = Message(
                message_id=str(uuid.uuid4()),
                message_type=f"response_{original_message_data.get('message_type')}",
                sender=original_message_data.get('recipient'),
                recipient=original_message_data.get('sender'),
                payload=response_data
            )
            
            # Send response
            return self.send_message(response_message)
            
        except Exception as e:
            logger.error(
                "message_queue.response.failed",
                extra={
                    "original_message_id": original_message_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
    
    def get_message_status(self, message_id: str) -> Optional[str]:
        """Get message status"""
        try:
            message_key = f"{self.message_prefix}{message_id}"
            return self.redis_client.hget(message_key, 'status')
        except Exception as e:
            logger.error(
                "message_queue.get_status.failed",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return None
    
    def cleanup_expired_messages(self) -> int:
        """Clean up expired messages"""
        try:
            cleaned_count = 0
            
            for key in self.redis_client.scan_iter(f"{self.message_prefix}*"):
                message_data = self.redis_client.hgetall(key)
                created_at = message_data.get('created_at')
                
                if created_at:
                    created_time = datetime.fromisoformat(created_at)
                    if (datetime.utcnow() - created_time).total_seconds() > self.timeout * 2:
                        self.redis_client.delete(key)
                        cleaned_count += 1
            
            logger.info(
                "message_queue.cleanup.success",
                extra={
                    "cleaned_count": cleaned_count
                }
            )
            return cleaned_count
            
        except Exception as e:
            logger.error(
                "message_queue.cleanup.failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return 0
    
    def get_queue_length(self, recipient: str) -> int:
        """Get queue length for a recipient"""
        try:
            queue_key = f"{self.queue_prefix}{recipient}"
            return self.redis_client.llen(queue_key)
        except Exception as e:
            logger.error(
                "message_queue.get_queue_length.failed",
                extra={
                    "recipient": recipient,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return 0
