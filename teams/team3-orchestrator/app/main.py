from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
import threading
from contextlib import asynccontextmanager

# Import routers
from .api import health, users, images, containers, auth

# Import services
from .services.service_discovery import ServiceDiscovery, ServiceInfo
from .services.message_processor import MessageProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services
service_discovery = None
message_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    global service_discovery, message_processor
    
    logger.info("Starting NVIDIA Orchestrator...")
    
    # Initialize service discovery
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    service_discovery = ServiceDiscovery(redis_host, redis_port, redis_db=0)
    message_processor = MessageProcessor(redis_host, redis_port, redis_db=1)
    
    # Register orchestrator service
    orchestrator_service = ServiceInfo(
        service_id=f"orchestrator-{int(time.time())}",
        service_type="orchestrator",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "3003")),
        health_endpoint="/health",
        metadata={
            "version": "1.0.0",
            "capabilities": ["container_management", "image_management", "docker_integration"]
        }
    )
    
    if service_discovery.register_service(orchestrator_service):
        logger.info(f"Orchestrator registered: {orchestrator_service.service_id}")
    else:
        logger.error("Failed to register orchestrator service")
    
    # Start message processor
    message_processor.start()
    logger.info("Message processor started")
    
    # Start heartbeat thread
    def heartbeat_worker():
        while True:
            try:
                if service_discovery:
                    service_discovery.update_heartbeat(orchestrator_service.service_id)
                time.sleep(10)  # Update heartbeat every 10 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(30)  # Wait longer on error
    
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    logger.info("Heartbeat thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NVIDIA Orchestrator...")
    
    if message_processor:
        message_processor.stop()
        logger.info("Message processor stopped")
    
    if service_discovery and orchestrator_service:
        service_discovery.deregister_service("orchestrator", orchestrator_service.service_id)
        logger.info("Orchestrator deregistered")

# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Orchestrator",
    description="Container and Image Orchestration Service with Service Discovery",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(containers.router, prefix="/api/containers", tags=["containers"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Orchestrator with Service Discovery and Message Queue",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "users": "/api/users",
            "images": "/api/images",
            "containers": "/api/containers",
            "auth": "/api/auth"
        }
    }

@app.get("/api/orchestrator/status")
async def get_status():
    """Get orchestrator status including service discovery and message queue"""
    try:
        status = {
            "service": "orchestrator",
            "status": "healthy",
            "timestamp": time.time()
        }
        
        if service_discovery:
            status["service_discovery"] = "connected"
        else:
            status["service_discovery"] = "disconnected"
        
        if message_processor:
            status["message_processor"] = "running"
            status["queue_length"] = message_processor.message_queue.get_queue_length(
                message_processor.service_id
            )
        else:
            status["message_processor"] = "stopped"
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "service": "orchestrator",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3003"))
    
    logger.info(f"Starting Orchestrator on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


