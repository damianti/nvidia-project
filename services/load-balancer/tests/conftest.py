import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, Mock

from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache
from app.services.service_selector import RoundRobinSelector
from app.schemas.service_info import ServiceInfo


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    """Fresh CircuitBreaker per test."""
    return CircuitBreaker()


@pytest.fixture
def fallback_cache() -> FallbackCache:
    """Fresh FallbackCache per test."""
    return FallbackCache(ttl_seconds=1.0)


@pytest.fixture
def service_selector() -> RoundRobinSelector:
    """RoundRobin selector fixture."""
    return RoundRobinSelector()


@pytest.fixture
def sample_service_info() -> List[ServiceInfo]:
    """Sample services for selection and cache tests."""
    return [
        ServiceInfo(
            container_id="svc-1",
            container_ip="10.0.0.2",
            internal_port=80,
            external_port=30000,
            status="passing",
            image_id=1,
            app_hostname="example.com",
        ),
        ServiceInfo(
            container_id="svc-2",
            container_ip="10.0.0.3",
            internal_port=80,
            external_port=30001,
            status="passing",
            image_id=1,
            app_hostname="example.com",
        ),
    ]


@pytest.fixture
def expired_timestamp() -> datetime:
    """Timestamp in the past to force cache expiration."""
    return datetime.now() - timedelta(seconds=5)


@pytest.fixture
def mock_discovery_client(sample_service_info: List[ServiceInfo]) -> AsyncMock:
    """Mock ServiceDiscoveryClient with async get_healthy_services."""
    client = AsyncMock()
    client.get_healthy_services = AsyncMock(return_value=sample_service_info)
    return client


@pytest.fixture
def mock_circuit_breaker(sample_service_info: List[ServiceInfo]) -> Mock:
    """Mock circuit breaker with call method."""
    breaker = Mock()
    breaker.call = AsyncMock(return_value=sample_service_info)
    breaker.get_state = Mock(return_value=Mock(value="CLOSED"))
    return breaker


@pytest.fixture
def mock_fallback_cache(sample_service_info: List[ServiceInfo]) -> Mock:
    """Mock fallback cache with async methods."""
    cache = Mock()
    cache.update = AsyncMock()
    cache.get = AsyncMock(return_value=sample_service_info)
    return cache


@pytest.fixture
def dummy_request_factory():
    """Factory to create mock FastAPI requests with JSON body bytes."""
    import json

    def factory(payload: dict | None):
        req = Mock()

        async def body():
            if payload is None:
                return b""
            return json.dumps(payload).encode()

        req.body = AsyncMock(side_effect=body)
        return req

    return factory
