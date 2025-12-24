"""
Tests for proxy_service - Extended tests to complement existing ones
"""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx

from app.services import proxy_service
from app.services.routing_cache import Cache, CacheEntry
from datetime import datetime, timedelta


class TestProxyServiceExtended:
    """Extended tests for proxy_service to complement existing tests"""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client"""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return Cache()

    @pytest.mark.asyncio
    async def test_proxy_to_container_502_error_invalidates_cache(
        self, mock_http_client, cache
    ):
        """Test that 502 error invalidates cache"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.content = b"Bad Gateway"
        mock_response.headers = {}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800),
        )
        cache.set("testapp.localhost", "127.0.0.1", entry)

        result = await proxy_service.proxy_to_container(
            http_client=mock_http_client,
            method="GET",
            target_host="172.19.0.1",
            target_port=32768,
            headers={},
            body=b"",
            cached_memory=cache,
            app_hostname="testapp.localhost",
            client_ip="127.0.0.1",
            remaining_path="/",
        )

        assert result.status_code == 502
        # Cache should be invalidated for 5xx errors
        assert cache.get("testapp.localhost", "127.0.0.1") is None

    @pytest.mark.asyncio
    async def test_proxy_to_container_503_error_invalidates_cache(
        self, mock_http_client, cache
    ):
        """Test that 503 error invalidates cache"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.content = b"Service Unavailable"
        mock_response.headers = {}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800),
        )
        cache.set("testapp.localhost", "127.0.0.1", entry)

        result = await proxy_service.proxy_to_container(
            http_client=mock_http_client,
            method="GET",
            target_host="172.19.0.1",
            target_port=32768,
            headers={},
            body=b"",
            cached_memory=cache,
            app_hostname="testapp.localhost",
            client_ip="127.0.0.1",
            remaining_path="/",
        )

        assert result.status_code == 503
        assert cache.get("testapp.localhost", "127.0.0.1") is None

    @pytest.mark.asyncio
    async def test_proxy_to_container_4xx_does_not_invalidate_cache(
        self, mock_http_client, cache
    ):
        """Test that 4xx errors don't invalidate cache"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b"Not Found"
        mock_response.headers = {}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        entry = CacheEntry(
            target_host="172.19.0.1",
            target_port=32768,
            container_id="abc123",
            image_id=1,
            expires_at=datetime.now() + timedelta(seconds=1800),
        )
        cache.set("testapp.localhost", "127.0.0.1", entry)

        result = await proxy_service.proxy_to_container(
            http_client=mock_http_client,
            method="GET",
            target_host="172.19.0.1",
            target_port=32768,
            headers={},
            body=b"",
            cached_memory=cache,
            app_hostname="testapp.localhost",
            client_ip="127.0.0.1",
            remaining_path="/",
        )

        assert result.status_code == 404
        # Cache should NOT be invalidated for 4xx errors
        assert cache.get("testapp.localhost", "127.0.0.1") is not None

    @pytest.mark.asyncio
    async def test_proxy_to_container_empty_path(self, mock_http_client, cache):
        """Test proxy with empty path"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Success"
        mock_response.headers = {}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await proxy_service.proxy_to_container(
            http_client=mock_http_client,
            method="GET",
            target_host="172.19.0.1",
            target_port=32768,
            headers={},
            body=b"",
            cached_memory=cache,
            app_hostname="testapp.localhost",
            client_ip="127.0.0.1",
            remaining_path="",  # Empty path
        )

        assert result.status_code == 200
        # Should add leading slash
        call_args = mock_http_client.request.call_args
        assert call_args[1]["url"] == "http://172.19.0.1:32768/"
