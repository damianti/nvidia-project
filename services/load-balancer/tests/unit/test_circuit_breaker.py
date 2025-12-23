import asyncio
import pytest
from unittest.mock import AsyncMock

from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


@pytest.fixture
def short_breaker() -> CircuitBreaker:
    return CircuitBreaker(failure_threshold=2, reset_timeout=0.05)


@pytest.mark.asyncio
async def test_circuit_starts_closed(short_breaker: CircuitBreaker):
    assert short_breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_opens_after_threshold(short_breaker: CircuitBreaker):
    failing_call = AsyncMock(side_effect=Exception("boom"))

    with pytest.raises(Exception):
        await short_breaker.call(failing_call)
    assert short_breaker.get_state() == CircuitState.CLOSED

    with pytest.raises(Exception):
        await short_breaker.call(failing_call)
    assert short_breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_blocks_until_timeout(short_breaker: CircuitBreaker):
    failing_call = AsyncMock(side_effect=Exception("boom"))
    for _ in range(2):
        with pytest.raises(Exception):
            await short_breaker.call(failing_call)

    assert short_breaker.is_open()

    with pytest.raises(CircuitBreakerOpenError):
        await short_breaker.call(failing_call)

    await asyncio.sleep(0.06)
    success_call = AsyncMock(return_value="ok")
    result = await short_breaker.call(success_call)

    assert result == "ok"
    assert short_breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_failure_reopens(short_breaker: CircuitBreaker):
    failing_call = AsyncMock(side_effect=Exception("boom"))
    for _ in range(2):
        with pytest.raises(Exception):
            await short_breaker.call(failing_call)

    await asyncio.sleep(0.06)

    with pytest.raises(Exception):
        await short_breaker.call(failing_call)

    assert short_breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_success_resets_failure_count(short_breaker: CircuitBreaker):
    failing_call = AsyncMock(side_effect=Exception("boom"))
    success_call = AsyncMock(return_value="ok")

    with pytest.raises(Exception):
        await short_breaker.call(failing_call)

    result = await short_breaker.call(success_call)

    assert result == "ok"
    assert short_breaker.get_status()["failure_count"] == 0

