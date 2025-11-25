import pytest
from unittest.mock import AsyncMock
from freezegun import freeze_time
from datetime import datetime, timedelta

from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


@pytest.mark.asyncio
async def test_circuit_starts_closed(circuit_breaker):
    """Circuit breaker should start in CLOSED state"""
    assert circuit_breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_opens_after_threshold(circuit_breaker):
    """Circuit should open after reaching failure threshold"""
    failing_call = AsyncMock(side_effect=Exception("boom"))
    
    # First failure - should still be CLOSED
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_call)
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # Second failure - should still be CLOSED
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_call)
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # Third failure - should open (threshold is 3 by default)
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_call)
    assert circuit_breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_state_blocks_calls(circuit_breaker):
    """When OPEN, circuit should block calls and raise CircuitBreakerOpenError"""
    # Open the circuit by causing failures
    failing_call = AsyncMock(side_effect=Exception("boom"))
    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)
    
    assert circuit_breaker.get_state() == CircuitState.OPEN
    
    # Try to call when OPEN - should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        await circuit_breaker.call(failing_call)


@pytest.mark.asyncio
async def test_half_open_to_closed(circuit_breaker):
    """When HALF_OPEN and call succeeds, circuit should close"""
    # Use freeze_time from the start to control time
    with freeze_time("2024-01-01 12:00:00") as frozen_time:
        # Open the circuit
        failing_call = AsyncMock(side_effect=Exception("boom"))
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)
        
        assert circuit_breaker.get_state() == CircuitState.OPEN
        
        # Fast forward past reset timeout (15 seconds default)
        frozen_time.tick(timedelta(seconds=16))
        
        # Now a successful call should close the circuit
        success_call = AsyncMock(return_value="success")
        result = await circuit_breaker.call(success_call)
        
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_failure_reopens(circuit_breaker):
    """When HALF_OPEN and call fails, circuit should reopen"""
    # Use freeze_time from the start to control time
    with freeze_time("2024-01-01 12:00:00") as frozen_time:
        # Open the circuit
        failing_call = AsyncMock(side_effect=Exception("boom"))
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)
        
        assert circuit_breaker.get_state() == CircuitState.OPEN
        
        # Fast forward past reset timeout (15 seconds default)
        frozen_time.tick(timedelta(seconds=16))
        
        # Now a failing call should reopen the circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)
        
        assert circuit_breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_reset_timeout_transitions_to_half_open(circuit_breaker):
    """After reset_timeout, OPEN circuit should transition to HALF_OPEN"""
    # Use freeze_time from the start to control time
    with freeze_time("2024-01-01 12:00:00") as frozen_time:
        # Open the circuit
        failing_call = AsyncMock(side_effect=Exception("boom"))
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)
        
        assert circuit_breaker.get_state() == CircuitState.OPEN
        
        # Wait less than reset_timeout - should still be OPEN
        frozen_time.tick(timedelta(seconds=10))
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(failing_call)
        assert circuit_breaker.get_state() == CircuitState.OPEN
        
        # Wait past reset_timeout - should transition to HALF_OPEN
        frozen_time.tick(timedelta(seconds=6))  # Total 16 seconds from start
        # The call will fail, but circuit should be in HALF_OPEN first
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)
        # After failure in HALF_OPEN, it should reopen
        assert circuit_breaker.get_state() == CircuitState.OPEN


@pytest.mark.asyncio
async def test_successful_call_resets_failure_count(circuit_breaker):
    """Successful call should reset failure count even if circuit is CLOSED"""
    failing_call = AsyncMock(side_effect=Exception("boom"))
    success_call = AsyncMock(return_value="success")
    
    # Cause 2 failures
    for _ in range(2):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)
    
    # Successful call should reset failure count
    result = await circuit_breaker.call(success_call)
    assert result == "success"
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # Now we need 3 more failures to open (not just 1)
    for _ in range(2):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # Third failure should open
    with pytest.raises(Exception):
        await circuit_breaker.call(failing_call)
    assert circuit_breaker.get_state() == CircuitState.OPEN

