from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager
import threading
from dotenv import load_dotenv

from app.services.container_pool import ContainerPool
from app.services.kafka_consumer import KafkaConsumerService

from app import load_balancer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Load .env for local development (Docker Compose still injects envs at runtime)
    load_dotenv()
    logger.info("Starting NVIDIA Load Balancer...")
    # Create shared ContainerPool and expose it via app.state for routers
    container_pool = ContainerPool()
    app.state.container_pool = container_pool

    # Init Kafka consumer service with the shared pool
    consumer_service = KafkaConsumerService(container_pool)

    # Start consumer in background thread
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
    
    logger.info(f"Starting API gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


