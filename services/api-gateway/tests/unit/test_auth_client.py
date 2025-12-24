"""
Tests for AuthClient
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.clients.auth_client import AuthClient


class TestAuthClient:
    """Tests for AuthClient"""

    @pytest.fixture
    def auth_client(self):
        """Create AuthClient instance"""
        return AuthClient("http://auth-service:3005")

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client"""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_client, mock_http_client):
        """Test successful login"""
        auth_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token"}
        mock_http_client.request.return_value = mock_response

        login_data = {"email": "test@example.com", "password": "password123"}
        response = await auth_client.login(login_data)

        assert response.status_code == 200
        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/auth/login" in call_args[1]["url"]
        assert call_args[1]["json"] == login_data

    @pytest.mark.asyncio
    async def test_login_timeout(self, auth_client, mock_http_client):
        """Test login timeout"""
        auth_client.http_client = mock_http_client
        mock_http_client.request.side_effect = httpx.TimeoutException("Timeout")

        login_data = {"email": "test@example.com", "password": "password123"}

        with pytest.raises(httpx.TimeoutException):
            await auth_client.login(login_data)

    @pytest.mark.asyncio
    async def test_signup_success(self, auth_client, mock_http_client):
        """Test successful signup"""
        auth_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_http_client.request.return_value = mock_response

        signup_data = {
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser",
        }
        response = await auth_client.signup(signup_data)

        assert response.status_code == 200
        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/auth/signup" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_client, mock_http_client):
        """Test successful get current user"""
        auth_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_http_client.request.return_value = mock_response

        response = await auth_client.get_current_user(
            "Bearer token", {"access_token": "token"}
        )

        assert response.status_code == 200
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "/auth/me" in call_args[1]["url"]
        assert "Authorization" in call_args[1]["headers"]

    @pytest.mark.asyncio
    async def test_logout_success(self, auth_client, mock_http_client):
        """Test successful logout"""
        auth_client.http_client = mock_http_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.request.return_value = mock_response

        response = await auth_client.logout("token", {"access_token": "token"})

        assert response.status_code == 200
        call_args = mock_http_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/auth/logout" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_build_headers_with_correlation_id(self, auth_client):
        """Test building headers with correlation ID"""
        with patch("app.clients.auth_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = "test-correlation-id"
            headers = auth_client._build_headers()
            assert headers == {"X-Correlation-ID": "test-correlation-id"}

    @pytest.mark.asyncio
    async def test_build_headers_without_correlation_id(self, auth_client):
        """Test building headers without correlation ID"""
        with patch("app.clients.auth_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            headers = auth_client._build_headers()
            assert headers == {}
