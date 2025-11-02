from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import logging
import contextvars
import uuid

from app.utils.logger import correlation_id_var

logger = logging.getLogger("api-gateway")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch (self, request: Request, call_next):
        
        correlation_id = request.headers.get("correlation_id")
        if not correlation_id:
            correlation_id = uuid.uuid4().hex
            
        correlation_id_var.set(correlation_id)
            

        logger.info(f"request.received - {correlation_id_var.get()} {request.method} {request.url.path}")

        start = time.time()
        response = await call_next(request)

        process_time = (time.time() - start) * 1000
        logger.info(f"⬅️ request.completed - {correlation_id_var.get()} {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")


        return response