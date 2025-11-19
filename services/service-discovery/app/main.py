from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio


from app.utils.config import SERVICE_NAME, HOST, PORT

from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.services.kafka_consumer import KafkaConsumerService

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Starts the Kafka consumer as an asyncio task (not a thread).
    This is cleaner and more pythonic than using threading.
    """
    # Startup
    logger.info(
        "sd.startup",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    kafka_consumer = KafkaConsumerService()
    app.state.kafka_consumer = kafka_consumer

    # Start the consumer as an asyncio task
    consumer_task = asyncio.create_task(kafka_consumer.start())
    app.state.consumer_task = consumer_task
    
    yield
    
    # Shutdown
    logger.info(
        "sd.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    kafka_consumer.stop()
    
    # Wait for the consumer task to finish
    try:
        await asyncio.wait_for(consumer_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("kafka.consumer_stop_timeout")
        consumer_task.cancel()
  
# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA service-discovery",
    description="Service discovery for user services",
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


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics(request: Request):
    consumer = request.app.state.kafka_consumer
    return {
        "messages_processed": consumer.message_count,
        "registration_success": consumer.registration_success,
        "registration_failures": consumer.registration_failures,
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting sd on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


