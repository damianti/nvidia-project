from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from app.routes.load_balancer import router as load_balancer_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NVIDIA Load Balancer",
    description="Load Balancer with Service Discovery and Message Queue",
    version="1.0.0"
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
app.include_router(load_balancer_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Load Balancer with Service Discovery",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/load-balancer/health",
            "create_container": "/api/load-balancer/containers/create",
            "services": "/api/load-balancer/services",
            "stats": "/api/load-balancer/stats"
        }
    }

@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy", "service": "load-balancer"}

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3002"))
    
    logger.info(f"Starting Load Balancer on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
