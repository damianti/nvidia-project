from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

from app.services.kafka_consumer import KafkaConsumerService
from app.database.create_tables import create_tables
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Creates database tables and starts the Kafka consumer.
    """
    # Startup
    logger.info(
        "billing.startup",
        extra={
            "service_name": SERVICE_NAME,
        },
    )

    # Create database tables
    try:
        create_tables()
        logger.info("billing.database_tables_created")
    except Exception as e:
        logger.error(
            "billing.database_tables_creation_failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        # Don't fail startup - tables might already exist

    # Start Kafka consumer
    kafka_consumer = KafkaConsumerService()
    app.state.kafka_consumer = kafka_consumer

    kafka_task = asyncio.create_task(kafka_consumer.start())

    app.state.kafka_task = kafka_task

    yield

    # Shutdown
    logger.info(
        "billing.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        },
    )
    kafka_consumer.stop()

    try:
        await asyncio.wait_for(asyncio.gather(kafka_task), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("billing.shutdown_timeout")
        kafka_task.cancel()

