from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager
import threading
from dotenv import load_dotenv

from app.services.container_pool import ContainerPool
from app.services.kafka_consumer import KafkaConsumerService
from app.services.website_mapping import WebsiteMapping
from app import load_balancer
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger

logger = setup_logger("load-balancer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    logger.info("Starting NVIDIA Load Balancer...")
    
    container_pool = ContainerPool()
    website_map = WebsiteMapping()
    app.state.container_pool = container_pool
    app.state.website_map = website_map
    
    consumer_service = KafkaConsumerService(container_pool, website_map)

    
    def run_consumer():
        consumer_service.start()

    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield
    
    # Shutdown
    logger.info("Shutting down Load Balancer...")
    consumer_service.stop()


    
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Load Balancer",
    description="Load Balancer for cloud services",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(load_balancer.router, tags=["load_balancer"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Load Balancer",
        "version": "1.0.0",
        "endpoints": {
            "GET /pool": "Inspect in-memory pool state",
            "GET /route/{image_id}": "Select next running container for the image"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting Load Balancer on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


