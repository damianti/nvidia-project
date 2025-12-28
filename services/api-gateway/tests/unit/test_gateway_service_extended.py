"""
Extended tests for gateway_service
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request, Response

from app.services import gateway_service
from app.services.routing_cache import Cache, CacheEntry
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache
from app.services.metrics_collector import MetricsCollector
from app.clients.lb_client import LoadBalancerClient
from datetime import datetime, timedelta


class TestGatewayServiceExtended:
    """Extended tests for gateway_service"""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request"""
        request = Mock(spec=Request)
        request.method = "GET"
        request.headers = {"Host": "testapp.localhost"}
        request.body = AsyncMock(return_value=b"")
        return request

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client"""
        return AsyncMock()

    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return Cache()

    @pytest.fixture
    def mock_lb_client(self):
        """Mock LoadBalancerClient"""
        return Mock(spec=LoadBalancerClient)

    @pytest.mark.asyncio
    async def test_handle_route_request_success(
        self,
        mock_request: Mock,
        mock_http_client: AsyncMock,
        cache: Cache,
        mock_lb_client: Mock,
    ) -> None:
        """Test successful route request (Happy Path).

        Verifies:
        - Route is resolved correctly
        - Request is proxied to container
        - Response is returned

        Args:
            mock_request: Mock FastAPI Request
            mock_http_client: Mocked HTTP client
            cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
        """
        # Arrange
        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800),
        )
        cache.set("testapp.localhost", "127.0.0.1", entry)

        mock_proxy_response = Response(content=b"Success", status_code=200)
        mock_request.client.host = "127.0.0.1"

        with patch(
            "app.services.gateway_service.resolve_route", return_value=entry
        ), patch(
            "app.services.gateway_service.proxy_to_container",
            return_value=mock_proxy_response,
        ) as mock_proxy, patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ):
            user_id_cache = UserIdCache()
            container_user_cache = ContainerUserCache()
            metrics_collector = MetricsCollector()

            # Act
            result = await gateway_service.handle_route_request(
                request=mock_request,
                app_hostname="testapp.localhost",
                remaining_path="/",
                http_client=mock_http_client,
                cached_memory=cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                container_user_cache=container_user_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            assert result.status_code == 200
            mock_proxy.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_route_request_not_found(
        self,
        mock_request: Mock,
        mock_http_client: AsyncMock,
        cache: Cache,
        mock_lb_client: Mock,
    ) -> None:
        """Test route request when app not found (Error Case 3: Not Found).

        Verifies:
        - 503 status code is returned
        - Appropriate error message

        Args:
            mock_request: Mock FastAPI Request
            mock_http_client: Mocked HTTP client
            cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
        """
        # Arrange
        mock_request.client.host = "127.0.0.1"

        with patch(
            "app.services.gateway_service.resolve_route", return_value=None
        ), patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ):
            user_id_cache = UserIdCache()
            container_user_cache = ContainerUserCache()
            metrics_collector = MetricsCollector()

            # Act
            result = await gateway_service.handle_route_request(
                request=mock_request,
                app_hostname="nonexistent.localhost",
                remaining_path="/",
                http_client=mock_http_client,
                cached_memory=cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                container_user_cache=container_user_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            assert result.status_code == 503
            assert (
                "not found" in result.body.decode().lower()
                or "not available" in result.body.decode().lower()
            )

    @pytest.mark.asyncio
    async def test_handle_route_request_path_without_slash(
        self,
        mock_request: Mock,
        mock_http_client: AsyncMock,
        cache: Cache,
        mock_lb_client: Mock,
    ) -> None:
        """Test route request with path that doesn't start with slash (Edge Case).

        Verifies:
        - Path is normalized to start with '/'
        - Request is proxied correctly

        Args:
            mock_request: Mock FastAPI Request
            mock_http_client: Mocked HTTP client
            cache: Cache instance
            mock_lb_client: Mocked Load Balancer client
        """
        # Arrange
        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800),
        )
        cache.set("testapp.localhost", "127.0.0.1", entry)

        mock_proxy_response = Response(content=b"Success", status_code=200)
        mock_request.client.host = "127.0.0.1"

        with patch(
            "app.services.gateway_service.resolve_route", return_value=entry
        ), patch(
            "app.services.gateway_service.proxy_to_container",
            return_value=mock_proxy_response,
        ) as mock_proxy, patch(
            "app.services.gateway_service.extract_client_ip", return_value="127.0.0.1"
        ), patch(
            "app.services.gateway_service.prepare_proxy_headers", return_value={}
        ):
            user_id_cache = UserIdCache()
            container_user_cache = ContainerUserCache()
            metrics_collector = MetricsCollector()

            # Act
            result = await gateway_service.handle_route_request(
                request=mock_request,
                app_hostname="testapp.localhost",
                remaining_path="api/test",  # No leading slash
                http_client=mock_http_client,
                cached_memory=cache,
                lb_client=mock_lb_client,
                user_id_cache=user_id_cache,
                container_user_cache=container_user_cache,
                metrics_collector=metrics_collector,
            )

            # Assert
            assert result.status_code == 200
            # Verify that proxy_to_container was called with normalized path
            call_kwargs = mock_proxy.call_args[1]
            assert call_kwargs["remaining_path"] == "/api/test"
