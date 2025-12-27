from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database.config import engine
from app.database.models import Base
from app.services.kafka_producer import KafkaProducerSingleton
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("orchestrator.startup")

    try:
        logger.info("Creating/updating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/updated successfully")
    except Exception as e:
        logger.error(
            "database.setup.failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise

    yield

    # Shutdown
    logger.info("orchestrator.shutdown")
    KafkaProducerSingleton.instance().flush(5)

