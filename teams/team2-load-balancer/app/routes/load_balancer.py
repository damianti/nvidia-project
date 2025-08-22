from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import logging
import json
from typing import Dict, Any
from ..services.load_balancer_service import LoadBalancerService
from ..services.message_queue import MessageType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/load-balancer", tags=["load-balancer"])

# Initialize load balancer service
load_balancer = LoadBalancerService()

@router.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    try:
        # Update heartbeat
        load_balancer.update_heartbeat()
        
        # Get service stats
        stats = load_balancer.get_service_stats()
        
        return {
            "status": "healthy",
            "service_id": load_balancer.service_id,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/containers/create")
async def create_container_async(request: Request):
    """Create container asynchronously via message queue"""
    try:
        data = await request.json()
        image_name = data.get("image_name")
        tag = data.get("tag", "latest")
        min_instances = data.get("min_instances", 1)
        max_instances = data.get("max_instances", 3)
        
        if not image_name:
            raise HTTPException(status_code=400, detail="image_name is required")
        
        # Send async request
        message_id = load_balancer.create_container_async(
            image_name=image_name,
            tag=tag,
            min_instances=min_instances,
            max_instances=max_instances
        )
        
        return {
            "message": "Container creation request sent",
            "message_id": message_id,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to create container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_id}/start")
async def start_container_async(container_id: str):
    """Start container asynchronously via message queue"""
    try:
        # Send async request
        message_id = load_balancer.start_container_async(container_id)
        
        return {
            "message": "Container start request sent",
            "message_id": message_id,
            "container_id": container_id,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_id}/stop")
async def stop_container_async(container_id: str):
    """Stop container asynchronously via message queue"""
    try:
        # Send async request
        message_id = load_balancer.stop_container_async(container_id)
        
        return {
            "message": "Container stop request sent",
            "message_id": message_id,
            "container_id": container_id,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}/status")
async def get_message_status(message_id: str):
    """Get status of a message"""
    try:
        status = load_balancer.get_message_status(message_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {
            "message_id": message_id,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get message status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/responses")
async def get_responses():
    """Get response messages"""
    try:
        responses = load_balancer.receive_responses()
        
        return {
            "responses": [
                {
                    "message_id": msg.message_id,
                    "message_type": msg.message_type,
                    "sender": msg.sender,
                    "payload": msg.payload,
                    "status": msg.status,
                    "created_at": msg.created_at,
                    "processed_at": msg.processed_at
                }
                for msg in responses
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get responses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_available_services():
    """Get all available services from service discovery"""
    try:
        stats = load_balancer.get_service_stats()
        
        return {
            "load_balancer_id": stats["load_balancer_id"],
            "available_services": stats["available_services"],
            "queue_length": stats["queue_length"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/route/{service_type}")
async def route_to_service(service_type: str, request: Request):
    """Route request to a specific service type"""
    try:
        # Get request data
        method = request.method
        path = str(request.url.path).replace(f"/api/load-balancer/route/{service_type}", "")
        headers = dict(request.headers)
        
        # Remove headers that shouldn't be forwarded
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                body = await request.body()
        
        # Route request
        result = load_balancer.route_request(
            service_type=service_type,
            path=path,
            method=method,
            data=body,
            headers=headers
        )
        
        return JSONResponse(
            content=result["data"],
            status_code=result["status_code"]
        )
        
    except Exception as e:
        logger.error(f"Failed to route request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_dead_services():
    """Clean up dead services"""
    try:
        cleaned_count = load_balancer.cleanup_dead_services()
        
        return {
            "message": f"Cleaned up {cleaned_count} dead services",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """Get load balancer statistics"""
    try:
        stats = load_balancer.get_service_stats()
        
        return {
            "load_balancer": {
                "service_id": stats["load_balancer_id"],
                "queue_length": stats["queue_length"]
            },
            "services": stats["available_services"],
            "timestamp": "2024-01-01T00:00:00Z"  # You can add actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
