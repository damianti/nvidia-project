from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database.models import Base
from app.database.config import engine
from app.setup import create_default_user_if_needed
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "auth.startup",
        extra={
            "service_name": SERVICE_NAME,
        },
    )
    
    try:
        Base.metadata.create_all(bind=engine)
        create_default_user_if_needed()
    except Exception as e:
        logger.error(
            "auth.startup.database_error",
            extra={"error": str(e), "service_name": SERVICE_NAME},
            exc_info=True,
        )
        raise
    
    yield
    
    # Shutdown
    logger.info(
        "auth.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        },
    )

