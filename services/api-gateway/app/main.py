from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager
import asyncio

from app.routing_cache import Cache
from app import proxy
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger

logger = setup_logger("api-gateway")

async def clear_cache(cached_memory: Cache):
    """Background task que limpia entradas expiradas del cache periódicamente"""
    while True:
        try:
            count = cached_memory.clear_expired()
            if count > 0:
                logger.info(f"Cleaned {count} expired cache entries")
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
        
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup    
    logger.info("Starting NVIDIA API gateway...")
    cache = Cache()
    app.state.cached_memory = cache
    task = asyncio.create_task(clear_cache(cache))
    app.state.cleanup_task = task
    yield
    
    # Shutdown
    if hasattr(app.state, 'cleanup_task'):
        cleanup_task = app.state.cleanup_task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down API gateway...")
    


# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA API gateway",
    description="API gateway for cloud services",
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


