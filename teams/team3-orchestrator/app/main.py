from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
import threading
from contextlib import asynccontextmanager
from .database.config import engine
from .database.models import Base

# Import routers
from .api import health, users, images, containers, auth

# Import services
# from .services.service_discovery import ServiceDiscovery, ServiceInfo
# from .services.message_processor import MessageProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services
# service_discovery = None
# message_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting NVIDIA Orchestrator...")
    
    try:
        logger.info("Creating/updating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/updated successfully")
    
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


    yield
    
    # Shutdown
    logger.info("Shutting down NVIDIA Orchestrator...")
    
  
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Orchestrator",
    description="Container and Image Orchestration Service",
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


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3003"))
    
    logger.info(f"Starting Orchestrator on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


