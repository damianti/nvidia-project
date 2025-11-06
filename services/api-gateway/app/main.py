from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import httpx

from app.services.routing_cache import Cache
from app.routes.proxy_routes import router as proxy_router
from app.routes.auth_routes import router as auth_router
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import (
    CACHE_CLEANUP_INTERVAL,
    AUTH_SERVICE_URL,
    LOAD_BALANCER_URL,
    ORCHESTRATOR_URL,
    HOST,
    PORT
)
from app.clients.lb_client import LoadBalancerClient
from app.clients.orchestrator_client import OrchestratorClient
from app.clients.auth_client import AuthClient

logger = setup_logger("api-gateway")

# TODO put this function in corresponding file
async def clear_cache(cached_memory: Cache):
    """Background task que limpia entradas expiradas del cache periódicamente"""
    while True:
        try:
            count = cached_memory.clear_expired()
            if count > 0:
                logger.info(
                    "cache.cleanup.completed",
                    extra={
                        "entries_removed": count
                    }
                )
        except Exception as e:
            logger.error(
                "cache.cleanup.error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
        
        await asyncio.sleep(CACHE_CLEANUP_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup    
    

    logger.info("gateway.starting")

    http_client = httpx.AsyncClient(follow_redirects=True)
    app.state.http_client = http_client
    app.state.lb_client = LoadBalancerClient(LOAD_BALANCER_URL, http_client)
    app.state.orchestrator_client = OrchestratorClient(ORCHESTRATOR_URL, http_client)
    app.state.auth_client = AuthClient(AUTH_SERVICE_URL, http_client)
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
    
    # Close HTTP client
    if hasattr(app.state, 'http_client'):
        await app.state.http_client.aclose()
    
    logger.info("gateway.shutting_down") 
    


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



app.include_router(proxy_router, tags=["proxy"])
app.include_router(auth_router, tags=["auth"])

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
    
    logger.info(
        "gateway.startup",
        extra={
            "host": HOST,
            "port": PORT
        }
    )
    uvicorn.run(app, host=HOST, port=PORT)


