from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.lifespan import lifespan
from app.core.config import TAGS_METADATA, APP_METADATA
from app.core.middleware import setup_middleware
from app.core.routers import setup_routers
from app.routes.health_routes import router as health_router
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME, HOST, PORT

logger = setup_logger(SERVICE_NAME)

limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    **APP_METADATA,
    lifespan=lifespan,
    tags_metadata=TAGS_METADATA,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure middleware and routers
setup_middleware(app)
setup_routers(app)
app.include_router(health_router, tags=["health"])


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "auth.run",
        extra={
            "host": HOST,
            "port": PORT,
            "service_name": SERVICE_NAME,
        },
    )
    uvicorn.run(app, host=HOST, port=PORT)
