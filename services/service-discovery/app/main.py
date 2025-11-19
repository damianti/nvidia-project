from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager



from app.utils.config import SERVICE_NAME, HOST, PORT

from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.services.kafka_consumer import KafkaConsumerService

logger = setup_logger(SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(
        "sd.startup",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    kafka_consumer = KafkaConsumerService()
    await kafka_consumer.start()

    app.state.kafka_consumer = kafka_consumer
    yield
    
    # Shutdown
    logger.info(
        "sd.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        }
    )
    await kafka_consumer.stop()
  
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
    return {"messages_processed": consumer.message_count}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting sd on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


