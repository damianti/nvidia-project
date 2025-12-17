import pytest

from app.services.circuit_breaker import CircuitBreaker
from app.services.fallback_cache import FallbackCache
from app.schemas.service_info import ServiceInfo


@pytest.fixture
def circuit_breaker():
    """Fixture providing a fresh CircuitBreaker instance for each test"""
    return CircuitBreaker()


@pytest.fixture
def fallback_cache():
    """Fixture providing a fresh FallbackCache instance for each test"""
    return FallbackCache()


@pytest.fixture
def sample_service_info():
    """Returns a list of sample ServiceInfo objects for testing"""
    return [
        ServiceInfo(
            container_id="test-container-1",
            container_ip="172.17.0.2",
            internal_port=80,
            external_port=32768,
            status="passing",
            image_id=1,
            app_hostname="example.com"
        ),
        ServiceInfo(
            container_id="test-container-2",
            container_ip="172.17.0.3",
            internal_port=80,
            external_port=32769,
            status="passing",
            image_id=1,
            app_hostname="example.com"
        )
    ]