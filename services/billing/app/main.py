from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio


from app.api.billing import router as billing_router
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME, HOST, PORT
from app.database.create_tables import create_tables

from app.services.kafka_consumer import KafkaConsumerService

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
        }
    )
    
    # Create database tables
    try:
        create_tables()
        logger.info("billing.database_tables_created")
    except Exception as e:
        logger.error(
            "billing.database_tables_creation_failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
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
        }
    )
    kafka_consumer.stop()
    
    try:
        await asyncio.wait_for(asyncio.gather(kafka_task), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("billing.shutdown_timeout")
        kafka_task.cancel()
  
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA Billing Service",
    description="Handles automated billing, invoice management, and cost tracking for user and platform services.",
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

app.include_router(billing_router, tags=["billing"])

@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics(request: Request):
    """Get billing service metrics"""
    consumer = request.app.state.kafka_consumer
    return {
        "messages_processed": consumer.message_count,
        "processed_success": consumer.processed_success,
        "processed_failures": consumer.processed_failures,
    }





if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "billing.startup",
        extra={
            "host": HOST,
            "port": PORT
        }
    )
    uvicorn.run(app, host=HOST, port=PORT)


