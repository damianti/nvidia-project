from fastapi import FastAPI

from app.core.lifespan import lifespan
from app.core.config import TAGS_METADATA, APP_METADATA
from app.core.middleware import setup_middleware
from app.core.routers import setup_routers
from app.routes.health_routes import router as health_router
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME, HOST, PORT

logger = setup_logger(SERVICE_NAME)

# Create FastAPI app
app = FastAPI(
    **APP_METADATA,
    lifespan=lifespan,
    tags_metadata=TAGS_METADATA,
)

# Configure middleware and routers
setup_middleware(app)
setup_routers(app)
app.include_router(health_router, tags=["health"])


if __name__ == "__main__":
    import uvicorn

    logger.info("orchestrator.startup", extra={"host": HOST, "port": PORT})
    uvicorn.run(app, host=HOST, port=PORT)
