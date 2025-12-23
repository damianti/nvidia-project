from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import uuid

from app.utils.logger import correlation_id_var, setup_logger

logger = setup_logger("orchestrator")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = uuid.uuid4().hex

        correlation_id_var.set(correlation_id)

        logger.info(
            "request.received",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.url.query) if request.url.query else None,
                "client_ip": request.client.host if request.client else None,
            },
        )

        start = time.time()
        try:
            response = await call_next(request)

            response.headers["X-Correlation-ID"] = correlation_id

            process_time = (time.time() - start) * 1000
            logger.info(
                "request.completed",
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time, 2),
                },
            )

            return response
        except Exception as e:
            process_time = (time.time() - start) * 1000
            logger.error(
                "request.failed",
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time_ms": round(process_time, 2),
                },
                exc_info=True,
            )
            raise
