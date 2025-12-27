from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

from app.services.kafka_consumer import KafkaConsumerService
from app.services.service_cache import ServiceCache
from app.services.consul_watcher import ConsulWatcher
from app.services.website_mapping import AppHostnameMapping
from app.utils.logger import setup_logger
from app.utils.config import SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


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
