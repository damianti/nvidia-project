import asyncio
from app.services.routing_cache import Cache
from app.utils.logger import setup_logger
from app.utils.config import CACHE_CLEANUP_INTERVAL, SERVICE_NAME

logger = setup_logger(SERVICE_NAME)


async def clear_cache_task(cached_memory: Cache) -> None:
    """Background task that periodically cleans expired entries from the cache."""
    while True:
        try:
            count = cached_memory.clear_expired()
            if count > 0:
                logger.info("cache.cleanup.completed", extra={"entries_removed": count})
        except Exception as e:
            logger.error(
                "cache.cleanup.error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )

        await asyncio.sleep(CACHE_CLEANUP_INTERVAL)


def start_cache_cleanup_task(cache: Cache) -> asyncio.Task:
    """Start the cache cleanup background task."""
    return asyncio.create_task(clear_cache_task(cache))


async def stop_cache_cleanup_task(task: asyncio.Task) -> None:
    """Stop the cache cleanup background task gracefully."""
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
