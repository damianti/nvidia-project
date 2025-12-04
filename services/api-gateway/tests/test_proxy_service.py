"""
Unit tests for proxy service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi import Response

from app.services.proxy_service import proxy_to_target


class TestProxyToTarget:
    """Tests for proxy_to_target function."""
    
    @pytest.mark.asyncio
    async def test_proxy_to_target_success(self):
        """Test successful proxy request."""
        # Setup mocks
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.content = b"Hello World"
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_client.request = AsyncMock(return_value=mock_response)
        
        # Test
        result = await proxy_to_target(
            http_client=mock_client,
            method="GET",
            target_url="http://example.com",
            headers={"Host": "example.com"},
            body=b""
        )
        
        # Assertions
        assert isinstance(result, Response)
        assert result.status_code == 200
        assert result.body == b"Hello World"
        mock_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_proxy_to_target_timeout(self):
        """Test proxy request timeout handling."""
        # Setup mocks
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        
        # Test
        result = await proxy_to_target(
            http_client=mock_client,
            method="GET",
            target_url="http://example.com",
            headers={},
            body=b""
        )
        
        # Assertions
        assert isinstance(result, Response)
        assert result.status_code == 504
        assert "timeout" in result.body.decode().lower()
    
    @pytest.mark.asyncio
    async def test_proxy_to_target_connection_error(self):
        """Test proxy request connection error handling."""
        # Setup mocks
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        # Test
        result = await proxy_to_target(
            http_client=mock_client,
            method="GET",
            target_url="http://example.com",
            headers={},
            body=b""
        )
        
        # Assertions
        assert isinstance(result, Response)
        assert result.status_code == 503
        assert "cannot connect" in result.body.decode().lower() or "unavailable" in result.body.decode().lower()
    
    @pytest.mark.asyncio
    async def test_proxy_to_target_post_with_body(self):
        """Test proxy POST request with body."""
        # Setup mocks
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.content = b"Created"
        mock_response.status_code = 201
        mock_response.headers = {}
        mock_client.request = AsyncMock(return_value=mock_response)
        
        # Test
        result = await proxy_to_target(
            http_client=mock_client,
            method="POST",
            target_url="http://example.com/api",
            headers={"Content-Type": "application/json"},
            body=b'{"key": "value"}'
        )
        
        # Assertions
        assert isinstance(result, Response)
        assert result.status_code == 201
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["content"] == b'{"key": "value"}'
    
    @pytest.mark.asyncio
    async def test_proxy_to_target_preserves_headers(self):
        """Test that response headers are preserved."""
        # Setup mocks
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.content = b"Content"
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "application/json",
            "X-Custom-Header": "value"
        }
        mock_client.request = AsyncMock(return_value=mock_response)
        
        # Test
        result = await proxy_to_target(
            http_client=mock_client,
            method="GET",
            target_url="http://example.com",
            headers={},
            body=b""
        )
        
        # Assertions
        assert "Content-Type" in result.headers
        assert "X-Custom-Header" in result.headers
        assert result.headers["X-Custom-Header"] == "value"

