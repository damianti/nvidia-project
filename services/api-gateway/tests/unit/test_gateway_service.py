"""
Unit tests for Gateway Service functions.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response

from app.services.gateway_service import handle_route_request
from app.services.routing_cache import Cache, CacheEntry
from app.services.user_id_cache import UserIdCache
from app.services.metrics_collector import MetricsCollector


@pytest.mark.unit
class TestGatewayService:
    """Test suite for Gateway Service functions."""

    @pytest.mark.asyncio
    async def test_handle_route_request_success(
        self,
        mock_http_client: AsyncMock,
        mock_cache: Cache,
        mock_lb_client: Mock,
        sample_cache_entry: CacheEntry,
    ) -> None:
        """Test successful route request handling (Happy Path).

        Verifies:
        - Route is resolved correctly
        - Request is proxied to container
        - Response is returned

        Args:
            mock_http_client: Mocked HTTP client
            mock_cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
            sample_cache_entry: Sample cache entry fixture
        """
        # Arrange

        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.body = AsyncMock(return_value=b"")
        mock_request.client.host = "127.0.0.1"

        mock_cache.set("testapp.localhost", "127.0.0.1", sample_cache_entry)

        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = b"Response content"
        mock_response.headers = {}

        user_id_cache = UserIdCache()
        metrics_collector = MetricsCollector()

        with patch(
            "app.services.gateway_service.resolve_route",
            return_value=sample_cache_entry,
        ), patch(
            "app.services.gateway_service.proxy_to_container",
            return_value=mock_response,
        ), patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ):

            # Act
            result = await handle_route_request(
                request=mock_request,
                app_hostname="testapp.localhost",
                remaining_path="/",
                http_client=mock_http_client,
                cached_memory=mock_cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_handle_route_request_not_found(
        self, mock_http_client: AsyncMock, mock_cache: Cache, mock_lb_client: Mock
    ) -> None:
        """Test route request when route is not found (Error Case 3: Not Found).

        Verifies:
        - 503 status code is returned
        - Appropriate error message

        Args:
            mock_http_client: Mocked HTTP client
            mock_cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        with patch(
            "app.services.gateway_service.resolve_route", return_value=None
        ), patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ):

            user_id_cache = UserIdCache()
            metrics_collector = MetricsCollector()

            # Act
            result = await handle_route_request(
                request=mock_request,
                app_hostname="nonexistent.localhost",
                remaining_path="/",
                http_client=mock_http_client,
                cached_memory=mock_cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            assert result.status_code == 503
            assert (
                "not found" in result.body.decode().lower()
                or "not available" in result.body.decode().lower()
            )

    @pytest.mark.asyncio
    async def test_handle_route_request_path_normalization(
        self,
        mock_http_client: AsyncMock,
        mock_cache: Cache,
        mock_lb_client: Mock,
        sample_cache_entry: CacheEntry,
    ) -> None:
        """Test that remaining_path is normalized to start with '/' (Edge Case).

        Verifies:
        - Path without leading slash is normalized
        - Request is proxied correctly

        Args:
            mock_http_client: Mocked HTTP client
            mock_cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
            sample_cache_entry: Sample cache entry fixture
        """
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.body = AsyncMock(return_value=b"")
        mock_request.client.host = "127.0.0.1"

        mock_response = Mock(spec=Response)
        mock_response.status_code = 200

        with patch(
            "app.services.gateway_service.resolve_route",
            return_value=sample_cache_entry,
        ), patch(
            "app.services.gateway_service.proxy_to_container",
            return_value=mock_response,
        ) as mock_proxy, patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ):

            user_id_cache = UserIdCache()
            metrics_collector = MetricsCollector()

            # Act
            await handle_route_request(
                request=mock_request,
                app_hostname="testapp.localhost",
                remaining_path="api/users",  # No leading slash
                http_client=mock_http_client,
                cached_memory=mock_cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            # Verify that proxy_to_container was called with normalized path
            call_kwargs = mock_proxy.call_args[1]
            assert call_kwargs["remaining_path"].startswith("/")
