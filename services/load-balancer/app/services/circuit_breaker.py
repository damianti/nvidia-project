import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class CircuitState(Enum):
    """Circuit Breaker states"""
    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Circuit is open, requests blocked (using fallback)
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    
    Protects against cascading failures when Service Discovery is down.
    
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
        failure_threshold: int = 3,
        reset_timeout: float = 15.0,
    ) -> None:
        """
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            reset_timeout: Seconds to wait before trying HALF_OPEN state
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """
        Execute a function with circuit breaker protection.
        
        Returns:
            Result of func(*args, **kwargs) if successful
        Raises:
            Exception if circuit is OPEN and no fallback available
        """
        async with self._lock:
            # Check if we can make the call
            if self._state == CircuitState.OPEN:
                # Check if enough time has passed to try HALF_OPEN
                if self._last_failure_time:
                    elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                    if elapsed >= self.reset_timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._failure_count = 0
                        logger.info(
                            "breaker.half_open",
                            extra={"elapsed_seconds": elapsed}
                        )
                    else:
                        # Still in OPEN state, raise exception
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker is OPEN. Retry after {self.reset_timeout - elapsed:.1f}s"
                        )
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        # Try to execute the function
        try:
            result = await func(*args, **kwargs)
            # Success - reset failure count and close circuit if needed
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    logger.info("breaker.closed", extra={"reason": "successful_request"})
                self._failure_count = 0
            return result
        except Exception as e:
            # Failure - increment count and potentially open circuit
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = datetime.now()
                
                if self._failure_count >= self.failure_threshold:
                    if self._state != CircuitState.OPEN:
                        self._state = CircuitState.OPEN
                        logger.warning(
                            "breaker.opened",
                            extra={
                                "failure_count": self._failure_count,
                                "threshold": self.failure_threshold
                            }
                        )
                elif self._state == CircuitState.HALF_OPEN:
                    # Failed in HALF_OPEN, go back to OPEN
                    self._state = CircuitState.OPEN
                    logger.warning("breaker.reopened", extra={"reason": "half_open_failed"})
            
            raise
    
    def is_open(self) -> bool:
        """Check if circuit is currently OPEN"""
        return self._state == CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    def get_status(self) -> dict:
        """Get circuit breaker status for debugging"""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "reset_timeout": self.reset_timeout,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN and request cannot proceed"""
    pass

