from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time
from contextlib import asynccontextmanager

from app import proxy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup    
    logger.info("Starting NVIDIA API gateway...")
    yield
    
    # Shutdown
    logger.info("Shutting down API gateway...")
    
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA API gateway",
    description="API gateway for cloud services",
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

app.include_router(proxy.router, tags=["proxy"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA API gateway",
        "version": "1.0.0",
        "endpoints": {

        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting API gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


