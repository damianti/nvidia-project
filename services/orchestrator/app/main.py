from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database.config import engine
from .database.models import Base

# Import routers
from .api import health, images, containers
from app.utils.config import SERVICE_NAME, HOST, PORT

# Import services
from .middleware.logging import LoggingMiddleware
from .services.kafka_producer import KafkaProducerSingleton


from app.utils.logger import setup_logger

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("orchestrator.startup")
    
    try:
        logger.info("Creating/updating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/updated successfully")
    
    except Exception as e:
        logger.error(
            "database.setup.failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise


    yield
    
    # Shutdown
    logger.info("orchestrator.shutdown")
    KafkaProducerSingleton.instance().flush(5)
  
# Tags metadata for Swagger organization
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints",
    },
    {
        "name": "images",
        "description": "Docker image management operations",
    },
    {
        "name": "containers",
        "description": "Container lifecycle management operations",
    },
]

# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Orchestrator",
    description="Container and Image Orchestration Service",
    version="1.0.0",
    lifespan=lifespan,
    tags_metadata=tags_metadata
)

app.add_middleware(LoggingMiddleware)
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
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(containers.router, prefix="/api/containers", tags=["containers"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Orchestrator with Service Discovery and Message Queue",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "images": "/api/images",
            "containers": "/api/containers",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "orchestrator.startup",
        extra={
            "host": HOST,
            "port": PORT
        }
    )
    uvicorn.run(app, host=HOST, port=PORT)


