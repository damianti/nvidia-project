"""
Fixtures for routing-related tests.
"""
from typing import Dict, Any
import pytest
from datetime import datetime, timedelta

from app.services.routing_cache import Cache, CacheEntry
from app.clients.lb_client import LoadBalancerClient
from app.clients.orchestrator_client import OrchestratorClient
from app.models.routing import RouteResult, RoutingInfo, LbError
from unittest.mock import AsyncMock, Mock
import httpx


@pytest.fixture
def sample_routing_info() -> RoutingInfo:
    """Fixture providing sample routing information.
    
    Returns:
        RoutingInfo object with container routing details.
    """
    return RoutingInfo(
        target_host="172.19.0.1",
        target_port=32768,
        container_id="abc123def456",
        image_id=1,
        ttl=1800  # Integer, not AsyncMock
    )


@pytest.fixture
def sample_cache_entry(sample_routing_info: RoutingInfo) -> CacheEntry:
    """Fixture providing a valid cache entry.
    
    Args:
        sample_routing_info: Routing info fixture.
    
    Returns:
        CacheEntry object with valid expiration time.
    """
    return CacheEntry(
        target_host=sample_routing_info.target_host,
        target_port=sample_routing_info.target_port,
        container_id=sample_routing_info.container_id,
        image_id=sample_routing_info.image_id,
        expires_at=datetime.now() + timedelta(seconds=1800)
    )


@pytest.fixture
def mock_lb_client() -> Mock:
    """Fixture providing a mocked LoadBalancerClient.
    
    Returns:
        Mock object configured as LoadBalancerClient with async route method.
    """
    client = Mock(spec=LoadBalancerClient)
    client.base_url = "http://load-balancer:3004"
    client.timeout_s = 0.5
    client.route = AsyncMock()
    return client


@pytest.fixture
def mock_orchestrator_client() -> Mock:
    """Fixture providing a mocked OrchestratorClient.
    
    Returns:
        Mock object configured as OrchestratorClient with async proxy_request method.
    """
    client = Mock(spec=OrchestratorClient)
    client.base_url = "http://orchestrator:3003"
    client.timeout_s = 30.0
    client.proxy_request = AsyncMock()
    return client


@pytest.fixture
def mock_cache() -> Cache:
    """Fixture providing a real Cache instance for testing.
    
    Returns:
        Cache instance (no mocking needed as it's in-memory).
    """
    return Cache()


@pytest.fixture
def mock_successful_routing_result(sample_routing_info: RoutingInfo) -> RouteResult:
    """Fixture providing a successful routing result.
    
    Args:
        sample_routing_info: Sample routing info fixture.
    
    Returns:
        RouteResult with ok=True and routing data.
    """
    # Ensure ttl is an integer, not a mock
    routing_info = RoutingInfo(
        target_host=sample_routing_info.target_host,
        target_port=sample_routing_info.target_port,
        container_id=sample_routing_info.container_id,
        image_id=sample_routing_info.image_id,
        ttl=1800  # Integer, not AsyncMock
    )
    return RouteResult(
        ok=True,
        data=routing_info,
        status_code=200
    )


@pytest.fixture
def mock_not_found_routing_result() -> RouteResult:
    """Fixture providing a not found routing result.
    
    Returns:
        RouteResult with ok=False and NOT_FOUND error.
    """
    return RouteResult(
        ok=False,
        error=LbError.NOT_FOUND,
        status_code=404,
        message="Website not found"
    )


@pytest.fixture
def mock_no_capacity_routing_result() -> RouteResult:
    """Fixture providing a no capacity routing result.
    
    Returns:
        RouteResult with ok=False and NO_CAPACITY error.
    """
    return RouteResult(
        ok=False,
        error=LbError.NO_CAPACITY,
        status_code=503,
        message="No containers available"
    )


@pytest.fixture
def sample_image_upload_data() -> Dict[str, Any]:
    """Fixture providing sample image upload form data.
    
    Returns:
        Dictionary with image upload parameters.
    """
    return {
        "name": "test-app",
        "tag": "latest",
        "app_hostname": "testapp.localhost",
        "container_port": 8080,
        "min_instances": 1,
        "max_instances": 2,
        "cpu_limit": "0.5",
        "memory_limit": "512m"
    }


@pytest.fixture
def sample_image_response() -> Dict[str, Any]:
    """Fixture providing sample image creation response.
    
    Returns:
        Dictionary representing an image object.
    """
    return {
        "id": 1,
        "name": "test-app",
        "tag": "latest",
        "app_hostname": "testapp.localhost",
        "status": "building",
        "user_id": 1
    }

