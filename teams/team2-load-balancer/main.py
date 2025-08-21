from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any

# Import routes
from app.routes.load_balancer import router as load_balancer_router

# Create FastAPI app instance
app = FastAPI(
    title="Load Balancer API",
    description="High-performance load balancer for the cloud platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(load_balancer_router)

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint to verify the load balancer is running"""
    return {
        "status": "healthy",
        "service": "load-balancer",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic information"""
    return {
        "message": "Load Balancer API is running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True
    )
