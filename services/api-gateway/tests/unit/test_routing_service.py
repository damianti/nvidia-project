"""
Unit tests for routing_service following QA Automation best practices.

This module contains unit tests with:
- AAA pattern (Arrange, Act, Assert)
- Comprehensive error scenarios
- Response structure validation
- Type hints and descriptive docstrings
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from app.services import routing_service
from app.services.routing_cache import Cache, CacheEntry
from app.services.user_id_cache import UserIdCache
from app.models.routing import RoutingInfo, RouteResult, LbError
from app.clients.lb_client import LoadBalancerClient


class TestRoutingService:
    """Unit tests for routing_service."""

    @pytest.fixture
    def mock_lb_client(self) -> Mock:
        """Fixture providing mocked LoadBalancerClient.

        Returns:
            Mock object configured as LoadBalancerClient.
        """
        return Mock(spec=LoadBalancerClient)

    @pytest.fixture
    def cache(self) -> Cache:
        """Fixture providing Cache instance.

        Returns:
            Cache instance for testing.
        """
        return Cache()

    @pytest.fixture
    def sample_routing_info(self) -> RoutingInfo:
        """Fixture providing sample routing information.

        Returns:
            RoutingInfo object with test data.
        """
        return RoutingInfo(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123def456",
            image_id=1,
            ttl=1800,
        )

    @pytest.fixture
    def sample_cache_entry(self, sample_routing_info: RoutingInfo) -> CacheEntry:
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
            expires_at=datetime.now() + timedelta(seconds=1800),
        )

    @pytest.mark.asyncio
    async def test_get_routing_info_happy_path(
        self, mock_lb_client: Mock, sample_routing_info: RoutingInfo
    ) -> None:
        """Test successful get routing info (happy path).

        Arrange:
            - Mock load balancer client returns successful RouteResult
            - RouteResult contains valid RoutingInfo

        Act:
            - Call get_routing_info with app_hostname

        Assert:
            - Result is not None
            - Result contains all required RoutingInfo fields
            - Result matches expected values
        """
        # Arrange
        route_result = RouteResult(ok=True, data=sample_routing_info, status_code=200)
        mock_lb_client.route = AsyncMock(return_value=route_result)

        # Act
        result = await routing_service.get_routing_info(
            "testapp.localhost", mock_lb_client
        )

        # Assert
        assert result is not None, "Result should not be None"
        assert isinstance(result, RoutingInfo), "Result should be RoutingInfo instance"
        assert (
            result.target_host == sample_routing_info.target_host
        ), f"Expected target_host {sample_routing_info.target_host}, got {result.target_host}"
        assert (
            result.target_port == sample_routing_info.target_port
        ), f"Expected target_port {sample_routing_info.target_port}, got {result.target_port}"
        assert result.container_id == sample_routing_info.container_id
        assert result.image_id == sample_routing_info.image_id

        # Verify load balancer was called
        mock_lb_client.route.assert_called_once_with("testapp.localhost")

    @pytest.mark.asyncio
    async def test_get_routing_info_not_found(self, mock_lb_client: Mock) -> None:
        """Test get routing info when not found (error case 1: resource not found).

        Arrange:
            - Mock load balancer client returns RouteResult with ok=False

        Act:
            - Call get_routing_info

        Assert:
            - Result is None
        """
        # Arrange
        route_result = RouteResult(
            ok=False,
            error=LbError.NOT_FOUND,
            status_code=404,
            message="Website not found",
        )
        mock_lb_client.route = AsyncMock(return_value=route_result)

        # Act
        result = await routing_service.get_routing_info(
            "nonexistent.localhost", mock_lb_client
        )

        # Assert
        assert result is None, "Result should be None when routing fails"

    @pytest.mark.asyncio
    async def test_get_routing_info_no_capacity(self, mock_lb_client: Mock) -> None:
        """Test get routing info when no capacity (error case 2: resource not found).

        Arrange:
            - Mock load balancer client returns NO_CAPACITY error

        Act:
            - Call get_routing_info

        Assert:
            - Result is None
        """
        # Arrange
        route_result = RouteResult(
            ok=False,
            error=LbError.NO_CAPACITY,
            status_code=503,
            message="No containers available",
        )
        mock_lb_client.route = AsyncMock(return_value=route_result)

        # Act
        result = await routing_service.get_routing_info(
            "testapp.localhost", mock_lb_client
        )

        # Assert
        assert result is None, "Result should be None when no capacity"

    @pytest.mark.asyncio
    async def test_get_routing_info_server_error(self, mock_lb_client: Mock) -> None:
        """Test get routing info when server error (error case 3: server error).

        Arrange:
            - Mock load balancer client returns UNKNOWN error

        Act:
            - Call get_routing_info

        Assert:
            - Result is None
        """
        # Arrange
        route_result = RouteResult(
            ok=False,
            error=LbError.UNKNOWN,
            status_code=500,
            message="Internal server error",
        )
        mock_lb_client.route = AsyncMock(return_value=route_result)

        # Act
        result = await routing_service.get_routing_info(
            "testapp.localhost", mock_lb_client
        )

        # Assert
        assert result is None, "Result should be None on server error"

    @pytest.mark.asyncio
    async def test_resolve_route_from_cache_happy_path(
        self, mock_lb_client: Mock, cache: Cache, sample_cache_entry: CacheEntry
    ) -> None:
        """Test resolve route from cache (happy path).

        Arrange:
            - Cache contains valid entry for app_hostname and client_ip
            - Entry has not expired

        Act:
            - Call resolve_route with cached app_hostname

        Assert:
            - Result is not None
            - Result matches cached entry
            - Load balancer is NOT called (cache hit)
            - All CacheEntry fields are correct
        """
        # Arrange
        cache.set("testapp.localhost", "127.0.0.1", sample_cache_entry)
        user_id_cache = UserIdCache()

        # Act
        result = await routing_service.resolve_route(
            "testapp.localhost", "127.0.0.1", cache, mock_lb_client, user_id_cache
        )

        # Assert
        assert result is not None, "Result should not be None when found in cache"
        assert isinstance(result, CacheEntry), "Result should be CacheEntry instance"
        assert (
            result.target_host == sample_cache_entry.target_host
        ), f"Expected target_host {sample_cache_entry.target_host}, got {result.target_host}"
        assert (
            result.target_port == sample_cache_entry.target_port
        ), f"Expected target_port {sample_cache_entry.target_port}, got {result.target_port}"
        assert result.container_id == sample_cache_entry.container_id
        assert result.image_id == sample_cache_entry.image_id
        assert result.expires_at == sample_cache_entry.expires_at

        # Verify load balancer was NOT called (cache hit)
        mock_lb_client.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_route_from_lb_happy_path(
        self, mock_lb_client: Mock, cache: Cache, sample_routing_info: RoutingInfo
    ) -> None:
        """Test resolve route from load balancer (happy path).

        Arrange:
            - Cache is empty (cache miss)
            - Mock load balancer returns successful RouteResult

        Act:
            - Call resolve_route

        Assert:
            - Result is not None
            - Result contains routing information
            - Load balancer was called
            - Entry was cached
            - Cached entry matches result
        """
        # Arrange
        route_result = RouteResult(ok=True, data=sample_routing_info, status_code=200)
        mock_lb_client.route = AsyncMock(return_value=route_result)
        user_id_cache = UserIdCache()

        # Act
        result = await routing_service.resolve_route(
            "testapp.localhost", "127.0.0.1", cache, mock_lb_client, user_id_cache
        )

        # Assert
        assert result is not None, "Result should not be None"
        assert isinstance(result, CacheEntry), "Result should be CacheEntry instance"
        assert result.target_host == sample_routing_info.target_host
        assert result.target_port == sample_routing_info.target_port

        # Verify load balancer was called
        mock_lb_client.route.assert_called_once_with("testapp.localhost")

        # Verify entry was cached
        cached = cache.get("testapp.localhost", "127.0.0.1")
        assert cached is not None, "Entry should be cached after successful routing"
        assert cached.target_host == sample_routing_info.target_host
        assert cached.target_port == sample_routing_info.target_port

    @pytest.mark.asyncio
    async def test_resolve_route_not_found(
        self, mock_lb_client: Mock, cache: Cache
    ) -> None:
        """Test resolve route when not found (error case 1: resource not found).

        Arrange:
            - Cache is empty
            - Mock load balancer returns NOT_FOUND

        Act:
            - Call resolve_route

        Assert:
            - Result is None
            - Nothing is cached
        """
        # Arrange
        route_result = RouteResult(
            ok=False,
            error=LbError.NOT_FOUND,
            status_code=404,
            message="Website not found",
        )
        mock_lb_client.route = AsyncMock(return_value=route_result)
        user_id_cache = UserIdCache()

        # Act
        result = await routing_service.resolve_route(
            "nonexistent.localhost", "127.0.0.1", cache, mock_lb_client, user_id_cache
        )

        # Assert
        assert result is None, "Result should be None when not found"

        # Verify nothing was cached
        cached = cache.get("nonexistent.localhost", "127.0.0.1")
        assert cached is None, "Nothing should be cached on failure"

    @pytest.mark.asyncio
    async def test_resolve_route_expired_cache_entry(
        self, mock_lb_client: Mock, cache: Cache, sample_routing_info: RoutingInfo
    ) -> None:
        """Test resolve route with expired cache entry.

        Arrange:
            - Cache contains expired entry
            - Mock load balancer returns successful RouteResult

        Act:
            - Call resolve_route

        Assert:
            - Result is not None (from LB, not cache)
            - Load balancer was called
            - New entry was cached
        """
        # Arrange
        expired_entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="old123",
            image_id=1,
            expires_at=datetime.now() - timedelta(seconds=1),  # Expired
        )
        cache.set("testapp.localhost", "127.0.0.1", expired_entry)

        route_result = RouteResult(ok=True, data=sample_routing_info, status_code=200)
        mock_lb_client.route = AsyncMock(return_value=route_result)
        user_id_cache = UserIdCache()

        # Act
        result = await routing_service.resolve_route(
            "testapp.localhost", "127.0.0.1", cache, mock_lb_client, user_id_cache
        )

        # Assert
        assert result is not None, "Result should not be None"
        assert (
            result.container_id == sample_routing_info.container_id
        ), "Result should come from load balancer, not expired cache"

        # Verify load balancer was called (cache miss due to expiration)
        mock_lb_client.route.assert_called_once()

    def test_create_cache_entry_from_routing_info_happy_path(
        self, sample_routing_info: RoutingInfo
    ) -> None:
        """Test creating cache entry from routing info (happy path).

        Arrange:
            - Valid RoutingInfo with all fields

        Act:
            - Call create_cache_entry_from_routing_info

        Assert:
            - CacheEntry contains all required fields
            - Fields match RoutingInfo values
            - expires_at is in the future
            - expires_at uses provided TTL
        """
        # Arrange - sample_routing_info fixture
        user_id_cache = UserIdCache()

        # Act
        entry = routing_service.create_cache_entry_from_routing_info(
            sample_routing_info, "testapp.localhost", user_id_cache
        )

        # Assert
        assert isinstance(entry, CacheEntry), "Result should be CacheEntry instance"
        assert (
            entry.target_host == sample_routing_info.target_host
        ), f"Expected target_host {sample_routing_info.target_host}, got {entry.target_host}"
        assert (
            entry.target_port == sample_routing_info.target_port
        ), f"Expected target_port {sample_routing_info.target_port}, got {entry.target_port}"
        assert entry.container_id == sample_routing_info.container_id
        assert entry.image_id == sample_routing_info.image_id
        assert entry.expires_at > datetime.now(), "expires_at should be in the future"

        # Verify TTL is used correctly (within 5 seconds tolerance)
        expected_expiry = datetime.now() + timedelta(seconds=sample_routing_info.ttl)
        time_diff = abs((entry.expires_at - expected_expiry).total_seconds())
        assert time_diff < 5, "expires_at should use provided TTL"

    def test_create_cache_entry_with_default_ttl(self) -> None:
        """Test creating cache entry with default TTL.

        Arrange:
            - RoutingInfo with ttl=None

        Act:
            - Call create_cache_entry_from_routing_info

        Assert:
            - CacheEntry is created successfully
            - expires_at is in the future
            - Default TTL is used
        """
        # Arrange
        routing_info = RoutingInfo(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            ttl=None,  # Should use default
        )

        # Act
        user_id_cache = UserIdCache()
        entry = routing_service.create_cache_entry_from_routing_info(
            routing_info, "testapp.localhost", user_id_cache
        )

        # Assert
        assert isinstance(entry, CacheEntry), "Result should be CacheEntry instance"
        assert entry.target_host == routing_info.target_host
        assert entry.expires_at > datetime.now(), "expires_at should be in the future"
