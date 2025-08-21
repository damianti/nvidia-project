from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import logging

from app.models.load_balancer import ServiceInfo, ContainerInfo, PortMapping, SystemServiceInfo
from app.services.load_balancer_service import load_balancer_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["load-balancer"])

@router.post("/services/{image_id}/register")
async def register_service(
    image_id: int,
    image_name: str,
    containers: List[ContainerInfo]
) -> Dict[str, str]:
    """Register a service with its containers"""
    try:
        await load_balancer_service.register_service(image_id, image_name, containers)
        return {"message": f"Service {image_name} registered successfully with {len(containers)} containers"}
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{image_id}")
async def get_service_info(image_id: int) -> ServiceInfo:
    """Get information about a specific service"""
    service = load_balancer_service.get_service_info(image_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service with image_id {image_id} not found")
    return service

@router.get("/services")
async def get_all_services() -> List[ServiceInfo]:
    """Get all registered services"""
    return load_balancer_service.get_all_services()

@router.get("/system-services")
async def get_system_services() -> List[SystemServiceInfo]:
    """Get all system services (orchestrator, billing)"""
    return load_balancer_service.get_system_services()

@router.get("/port-mappings")
async def get_port_mappings() -> List[PortMapping]:
    """Get all port mappings"""
    return load_balancer_service.get_port_mappings()

@router.api_route("/proxy/{image_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user_container_request(
    image_id: int,
    path: str,
    request: Request
) -> Response:
    """Proxy request to user container"""
    try:
        # Get request body
        body = await request.body()
        
        # Get headers (excluding host header)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Forward the request to user container
        full_path = f"/proxy/{image_id}/{path}"
        response = await load_balancer_service.forward_request(
            path=full_path,
            method=request.method,
            headers=headers,
            body=body
        )
        
        # Create response with same status and headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except ValueError as e:
        logger.error(f"Value error in proxy request: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in proxy request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_system_request(
    path: str,
    request: Request
) -> Response:
    """Proxy request to system services (orchestrator/billing) based on path"""
    try:
        # Get request body
        body = await request.body()
        
        # Get headers (excluding host header)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Forward the request using intelligent routing
        full_path = f"/{path}"
        response = await load_balancer_service.forward_request(
            path=full_path,
            method=request.method,
            headers=headers,
            body=body
        )
        
        # Create response with same status and headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except ValueError as e:
        logger.error(f"Value error in system proxy request: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in system proxy request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/health-check")
async def trigger_health_check() -> Dict[str, str]:
    """Trigger health check on all containers and system services"""
    try:
        await load_balancer_service.perform_health_checks()
        return {"message": "Health check completed"}
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_load_balancer_stats() -> Dict[str, Any]:
    """Get load balancer statistics"""
    services = load_balancer_service.get_all_services()
    system_services = load_balancer_service.get_system_services()
    port_mappings = load_balancer_service.get_port_mappings()
    
    total_containers = sum(len(service.containers) for service in services)
    healthy_containers = sum(
        len([c for c in service.containers if c.status.value == "healthy"])
        for service in services
    )
    total_requests = sum(service.total_requests for service in services)
    
    # System service stats
    healthy_system_services = sum(
        1 for service in system_services if service.status.value == "healthy"
    )
    total_system_requests = sum(service.total_requests for service in system_services)
    
    return {
        "user_services": {
            "total_services": len(services),
            "total_containers": total_containers,
            "healthy_containers": healthy_containers,
            "total_requests": total_requests,
        },
        "system_services": {
            "total_services": len(system_services),
            "healthy_services": healthy_system_services,
            "total_requests": total_system_requests,
        },
        "port_mappings_count": len(port_mappings)
    }
