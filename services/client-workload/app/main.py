from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import workload
from app.utils.config import SERVICE_NAME, PORT

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(SERVICE_NAME)

# Create FastAPI app
app = FastAPI(
    title="NVIDIA Client Workload Generator",
    description="Synthetic traffic generator for stress testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workload.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NVIDIA Client Workload Generator",
        "version": "1.0.0",
        "endpoints": {
            "POST /workload/start": "Start a new workload test",
            "POST /workload/stop/{test_id}": "Stop a running test",
            "GET /workload/status/{test_id}": "Get test status and metrics",
            "GET /workload/list": "List all tests",
            "GET /workload/metrics/{test_id}": "Get detailed metrics",
            "GET /workload/available-services": "Get available website URLs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

