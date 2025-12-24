"""
Tests for OrchestratorClient
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.clients.orchestrator_client import OrchestratorClient


class TestOrchestratorClient:
    """Tests for OrchestratorClient"""

    @pytest.fixture
    def orchestrator_client(self):
        """Create OrchestratorClient instance"""
        return OrchestratorClient("http://orchestrator:3003")

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client"""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_proxy_request_get(self, orchestrator_client, mock_http_client):
        """Test proxy GET request"""
        orchestrator_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1}
        mock_http_client.request.return_value = mock_response

        response = await orchestrator_client.proxy_request(
            method="GET", path="/api/images", query_params={"user_id": 1}
        )

        assert response.status_code == 200
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "/api/images" in call_args[1]["url"]
        assert "user_id=1" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_proxy_request_post_with_body(
        self, orchestrator_client, mock_http_client
    ):
        """Test proxy POST request with body"""
        orchestrator_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 201
        mock_http_client.request.return_value = mock_response

        body = b'{"name": "test"}'
        response = await orchestrator_client.proxy_request(
            method="POST",
            path="/api/images",
            body=body,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 201
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["content"] == body

    @pytest.mark.asyncio
    async def test_proxy_request_timeout(self, orchestrator_client, mock_http_client):
        """Test proxy request timeout"""
        orchestrator_client.http_client = mock_http_client
        mock_http_client.request.side_effect = httpx.TimeoutException("Timeout")

        with pytest.raises(httpx.TimeoutException):
            await orchestrator_client.proxy_request(method="GET", path="/api/images")

    @pytest.mark.asyncio
    async def test_proxy_request_exception(self, orchestrator_client, mock_http_client):
        """Test proxy request with general exception"""
        orchestrator_client.http_client = mock_http_client
        mock_http_client.request.side_effect = Exception("Connection error")

        with pytest.raises(Exception):
            await orchestrator_client.proxy_request(method="GET", path="/api/images")

    @pytest.mark.asyncio
    async def test_build_headers_with_correlation_id(self, orchestrator_client):
        """Test building headers with correlation ID"""
        with patch("app.clients.orchestrator_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = "test-correlation-id"
            headers = orchestrator_client._build_headers()
            assert headers == {"X-Correlation-ID": "test-correlation-id"}

    @pytest.mark.asyncio
    async def test_build_headers_without_correlation_id(self, orchestrator_client):
        """Test building headers without correlation ID"""
        with patch("app.clients.orchestrator_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            headers = orchestrator_client._build_headers()
            assert headers == {}
