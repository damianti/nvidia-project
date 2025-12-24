"""
Tests for auth_service
"""

import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException, Response, Request

from app.services import auth_service
from app.clients.auth_client import AuthClient
from app.schemas.user import LoginRequest, UserCreate


class TestAuthService:
    """Tests for auth_service"""

    @pytest.fixture
    def mock_auth_client(self):
        """Mock AuthClient"""
        return Mock(spec=AuthClient)

    @pytest.fixture
    def mock_response(self):
        """Mock FastAPI Response"""
        return Response()

    @pytest.mark.asyncio
    async def test_handle_login_success(self, mock_auth_client, mock_response):
        """Test successful login"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.headers = {"set-cookie": "access_token=test; HttpOnly"}
        mock_auth_response.json.return_value = {"access_token": "test-token"}
        mock_auth_client.login = AsyncMock(return_value=mock_auth_response)

        login_data = LoginRequest(email="test@example.com", password="password123")
        result = await auth_service.handle_login(
            login_data, mock_auth_client, mock_response
        )

        assert result == {"access_token": "test-token"}
        assert "Set-Cookie" in mock_response.headers

    @pytest.mark.asyncio
    async def test_handle_login_failure(self, mock_auth_client, mock_response):
        """Test login failure"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 401
        mock_auth_response.json.return_value = {"detail": "Invalid credentials"}
        mock_auth_client.login = AsyncMock(return_value=mock_auth_response)

        login_data = LoginRequest(email="test@example.com", password="wrong")

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.handle_login(login_data, mock_auth_client, mock_response)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_handle_signup_success(self, mock_auth_client, mock_response):
        """Test successful signup"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.headers = {"set-cookie": "access_token=test; HttpOnly"}
        mock_auth_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_auth_client.signup = AsyncMock(return_value=mock_auth_response)

        user_data = UserCreate(
            email="test@example.com", password="password123", username="testuser"
        )
        result = await auth_service.handle_signup(
            user_data, mock_auth_client, mock_response
        )

        assert result == {"id": 1, "email": "test@example.com"}
        assert "Set-Cookie" in mock_response.headers

    @pytest.mark.asyncio
    async def test_handle_signup_failure(self, mock_auth_client, mock_response):
        """Test signup failure"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 400
        mock_auth_response.json.return_value = {"detail": "Email already exists"}
        mock_auth_client.signup = AsyncMock(return_value=mock_auth_response)

        user_data = UserCreate(
            email="test@example.com", password="password123", username="testuser"
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.handle_signup(user_data, mock_auth_client, mock_response)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_get_current_user_success(self, mock_auth_client):
        """Test successful get current user"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_auth_response)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        result = await auth_service.handle_get_current_user(
            "Bearer token", mock_auth_client, mock_request
        )

        assert result == {"id": 1, "email": "test@example.com"}

    @pytest.mark.asyncio
    async def test_handle_get_current_user_failure(self, mock_auth_client):
        """Test get current user failure"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 401
        mock_auth_response.json.return_value = {"detail": "Invalid token"}
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_auth_response)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.handle_get_current_user(
                "Bearer invalid-token", mock_auth_client, mock_request
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_handle_logout_success(self, mock_auth_client, mock_response):
        """Test successful logout"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.headers = {"set-cookie": "access_token=; Max-Age=0"}
        mock_auth_response.json.return_value = {"message": "Logged out"}
        mock_auth_client.logout = AsyncMock(return_value=mock_auth_response)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {"access_token": "token"}

        result = await auth_service.handle_logout(
            "Bearer token", mock_auth_client, mock_response, mock_request
        )

        assert result == {"message": "Logged out"}
        assert "Set-Cookie" in mock_response.headers

    @pytest.mark.asyncio
    async def test_handle_logout_failure(self, mock_auth_client, mock_response):
        """Test logout failure"""
        mock_auth_response = Mock()
        mock_auth_response.status_code = 401
        mock_auth_response.json.return_value = {"detail": "Invalid token"}
        mock_auth_client.logout = AsyncMock(return_value=mock_auth_response)

        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.handle_logout(
                "Bearer invalid-token", mock_auth_client, mock_response, mock_request
            )

        assert exc_info.value.status_code == 401
