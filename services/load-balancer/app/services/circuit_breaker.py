"""
Circuit Breaker for Load Balancer.

State (CLOSED/OPEN/HALF_OPEN, failure count, last failure time) is stored in
Redis so all Load Balancer instances share the same view.
"""

import logging
from enum import Enum
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

_STATE_KEY = "lb:circuit:state"
_FAILURE_COUNT_KEY = "lb:circuit:failure_count"
_LAST_FAILURE_KEY = "lb:circuit:last_failure_time"


class CircuitState(Enum):
    """Circuit Breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation backed by Redis.

    States:
    - CLOSED: Normal operation, all requests go through
    - OPEN: Too many failures, requests blocked (use fallback)
    - HALF_OPEN: Testing if service recovered (allow 1 request)

    Transitions:
    - CLOSED -> OPEN: When failure_count >= failure_threshold
    - OPEN -> HALF_OPEN: After reset_timeout seconds
    - HALF_OPEN -> CLOSED: On successful request
    - HALF_OPEN -> OPEN: On failed request
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        failure_threshold: int = 3,
        reset_timeout: float = 15.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._redis = redis

    async def initialize(self) -> None:
        """Set default Redis keys if they don't already exist."""
        await self._redis.setnx(_STATE_KEY, CircuitState.CLOSED.value)
        await self._redis.setnx(_FAILURE_COUNT_KEY, "0")

    async def _get_state(self) -> CircuitState:
        val = await self._redis.get(_STATE_KEY)
        if val is None:
            return CircuitState.CLOSED
        return CircuitState(val)

    async def _set_state(self, state: CircuitState) -> None:
        await self._redis.set(_STATE_KEY, state.value)

    async def call(self, func, *args, **kwargs):
        """
        Execute a function with circuit breaker protection.

        Returns:
            Result of func(*args, **kwargs) if successful
        Raises:
            CircuitBreakerOpenError if circuit is OPEN
        """
        state = await self._get_state()

        if state == CircuitState.OPEN:
            last_failure_str = await self._redis.get(_LAST_FAILURE_KEY)
            if last_failure_str:
                last_failure = datetime.fromisoformat(last_failure_str)
                if last_failure.tzinfo is None:
                    last_failure = last_failure.replace(tzinfo=timezone.utc)
                elapsed = (datetime.now(timezone.utc) - last_failure).total_seconds()
                if elapsed >= self.reset_timeout:
                    await self._set_state(CircuitState.HALF_OPEN)
                    await self._redis.set(_FAILURE_COUNT_KEY, "0")
                    logger.info("breaker.half_open", extra={"elapsed_seconds": elapsed})
                    state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Retry after {self.reset_timeout - elapsed:.1f}s"
                    )
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if state == CircuitState.HALF_OPEN:
                await self._set_state(CircuitState.CLOSED)
                logger.info("breaker.closed", extra={"reason": "successful_request"})
            await self._redis.set(_FAILURE_COUNT_KEY, "0")
            return result
        except Exception:
            failure_count = await self._redis.incr(_FAILURE_COUNT_KEY)
            await self._redis.set(
                _LAST_FAILURE_KEY, datetime.now(timezone.utc).isoformat()
            )

            if failure_count >= self.failure_threshold:
                current_state = await self._get_state()
                if current_state != CircuitState.OPEN:
                    await self._set_state(CircuitState.OPEN)
                    logger.warning(
                        "breaker.opened",
                        extra={
                            "failure_count": failure_count,
                            "threshold": self.failure_threshold,
                        },
                    )
            elif state == CircuitState.HALF_OPEN:
                await self._set_state(CircuitState.OPEN)
                logger.warning("breaker.reopened", extra={"reason": "half_open_failed"})
            raise

    async def is_open(self) -> bool:
        """Check if circuit is currently OPEN."""
        return (await self._get_state()) == CircuitState.OPEN

    async def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return await self._get_state()

    async def get_status(self) -> dict:
        """Get circuit breaker status for debugging."""
        state = await self._get_state()
        failure_count = int((await self._redis.get(_FAILURE_COUNT_KEY)) or "0")
        last_failure_str: Optional[str] = await self._redis.get(_LAST_FAILURE_KEY)
        return {
            "state": state.value,
            "failure_count": failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": last_failure_str,
            "reset_timeout": self.reset_timeout,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN and request cannot proceed."""

    pass
