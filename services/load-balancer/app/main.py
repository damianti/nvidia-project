from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.services.service_discovery_client import ServiceDiscoveryClient
from app.services.service_selector import RoundRobinSelector
from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache
from app.routes import lb_routes
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import (
    HOST,
    PORT,
    SERVICE_NAME,
)
logger = setup_logger(SERVICE_NAME)

# Tags metadata for Swagger organization
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints",
    },
    {
        "name": "load_balancer",
        "description": "Load balancing and request routing operations",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    logger.info(
        "lb.startup",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    
    discovery_client = ServiceDiscoveryClient()
    service_selector = RoundRobinSelector()
    circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=15.0)
    fallback_cache = FallbackCache(ttl_seconds=10.0)
    
    app.state.discovery_client = discovery_client
    app.state.service_selector = service_selector
    app.state.circuit_breaker = circuit_breaker
    app.state.fallback_cache = fallback_cache
    yield
    
    # Shutdown
    logger.info(
        "lb.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    await discovery_client.close()


    
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Load Balancer",
    description="Load Balancer for cloud services",
    version="1.0.0",
    lifespan=lifespan,
    tags_metadata=tags_metadata
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

app.include_router(lb_routes.router, tags=["load_balancer"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Load Balancer",
        "version": "1.0.0",
        "endpoints": {
            "POST /route": "Route request to container by website_url"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "lb.run",
        extra={
            "host": HOST,
            "port": PORT,
            "service_name": SERVICE_NAME,
        }
    )
    uvicorn.run(app, host=HOST, port=PORT)


