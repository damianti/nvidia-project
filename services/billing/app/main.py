from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio


from app.api.billing import router as billing_router
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME, HOST, PORT

from app.services.kafka_consumer import KafkaConsumerService

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Starts the Kafka consumer as asyncio tasks.
    """
    # Startup
    logger.info(
        "billing.startup",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    
    
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
    consumer = request.app.state.kafka_consumer
    return None
    # return {
    #     "messages_processed": consumer.message_count,
    #     "registration_success": consumer.registration_success,
    #     "registration_failures": consumer.registration_failures,
    # }





if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting billing service on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


