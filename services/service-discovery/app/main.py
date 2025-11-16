from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


# Import routers
from .api import health, images, containers
from app.utils.config import SERVICE_NAME, HOST, PORT

# Import services
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("orchestrator.startup")

    yield
    
    # Shutdown
    logger.info("orchestrator.shutdown")
  
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Orchestrator",
    description="Container and Image Orchestration Service",
    version="1.0.0",
    lifespan=lifespan
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
    
    logger.info(f"Starting Orchestrator on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


