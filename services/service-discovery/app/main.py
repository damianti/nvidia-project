from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio


from app.api.services import router as services_router
from app.middleware.logging import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME, HOST, PORT

from app.services.kafka_consumer import KafkaConsumerService
from app.services.service_cache import ServiceCache
from app.services.consul_watcher import ConsulWatcher
from app.services.website_mapping import AppHostnameMapping

logger = setup_logger(SERVICE_NAME)

# Tags metadata for Swagger organization
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and diagnostic endpoints",
    },
    {
        "name": "services",
        "description": "Service discovery and health monitoring operations",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Starts the Kafka consumer and Consul watcher as asyncio tasks.
    """
    # Startup
    logger.info(
        "sd.startup",
        extra={
            "service_name": SERVICE_NAME,
        },
    )
    app_hostname_map = AppHostnameMapping()
    service_cache = ServiceCache(app_hostname_map)
    app.state.service_cache = service_cache
    app.state.app_hostname_map = app_hostname_map

    kafka_consumer = KafkaConsumerService()
    app.state.kafka_consumer = kafka_consumer

    consul_watcher = ConsulWatcher(service_cache)
    app.state.consul_watcher = consul_watcher

    kafka_task = asyncio.create_task(kafka_consumer.start())
    watcher_task = asyncio.create_task(consul_watcher.start())

    app.state.kafka_task = kafka_task
    app.state.watcher_task = watcher_task

    yield

    # Shutdown
    logger.info(
        "sd.shutdown",
        extra={
            "service_name": SERVICE_NAME,
        },
    )
    kafka_consumer.stop()
    consul_watcher.stop()

    try:
        await asyncio.wait_for(asyncio.gather(kafka_task, watcher_task), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("sd.shutdown_timeout")
        kafka_task.cancel()
        watcher_task.cancel()


# Create FastAPI app with lifespan
app = FastAPI(
    title="NVIDIA service-discovery",
    description="Service discovery for user services",
    version="1.0.0",
    lifespan=lifespan,
    tags_metadata=tags_metadata,
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

app.include_router(services_router, tags=["services"])


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

    logger.info("service_discovery.startup", extra={"host": HOST, "port": PORT})
    uvicorn.run(app, host=HOST, port=PORT)
