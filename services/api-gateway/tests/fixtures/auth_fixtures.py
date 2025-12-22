"""
Fixtures for authentication-related tests.
"""
from typing import Dict, Any
import pytest

from app.clients.auth_client import AuthClient
from unittest.mock import AsyncMock, Mock
import httpx


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Fixture providing sample user data for authentication tests.
    
    Returns:
        Dictionary containing user registration/login data.
    """
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "username": "testuser"
    }


@pytest.fixture
def sample_login_request() -> Dict[str, str]:
    """Fixture providing sample login request data.
    
    Returns:
        Dictionary with email and password for login.
    """
    return {
        "email": "test@example.com",
        "password": "testpass123"
    }


@pytest.fixture
def sample_user_response() -> Dict[str, Any]:
    """Fixture providing sample user response from auth service.
    
    Returns:
        Dictionary representing a user object with id, email, and username.
    """
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "created_at": "2025-01-01T00:00:00"
    }


@pytest.fixture
def sample_auth_token() -> str:
    """Fixture providing a sample JWT token.
    
    Returns:
        String representing a JWT access token.
    """
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjEwMjM5MDIyfQ.test"


@pytest.fixture
def mock_auth_client() -> Mock:
    """Fixture providing a mocked AuthClient.
    
    Returns:
        Mock object configured as AuthClient with async methods.
    """
    client = Mock(spec=AuthClient)
    client.base_url = "http://auth-service:3005"
    client.timeout_s = 30.0
    client.login = AsyncMock()
    client.signup = AsyncMock()
    client.get_current_user = AsyncMock()
    client.logout = AsyncMock()
    return client


@pytest.fixture
def mock_successful_auth_response(sample_user_response: Dict[str, Any]) -> Mock:
    """Fixture providing a mocked successful auth service response.
    
    Args:
        sample_user_response: Sample user response data.
    
    Returns:
        Mock httpx.Response with 200 status and user data.
    """
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {"set-cookie": "access_token=test-token; HttpOnly; Path=/"}
    response.json.return_value = sample_user_response
    return response


@pytest.fixture
def mock_error_response_400() -> Mock:
    """Fixture providing a mocked 400 Bad Request response.
    
    Returns:
        Mock httpx.Response with 400 status and error detail.
    """
    response = Mock(spec=httpx.Response)
    response.status_code = 400
    response.headers = {}
    response.json.return_value = {"detail": "Invalid request data"}
    return response


@pytest.fixture
def mock_error_response_401() -> Mock:
    """Fixture providing a mocked 401 Unauthorized response.
    
    Returns:
        Mock httpx.Response with 401 status and authentication error.
    """
    response = Mock(spec=httpx.Response)
    response.status_code = 401
    response.headers = {}
    response.json.return_value = {"detail": "Invalid credentials"}
    return response


@pytest.fixture
def mock_error_response_404() -> Mock:
    """Fixture providing a mocked 404 Not Found response.
    
    Returns:
        Mock httpx.Response with 404 status and not found error.
    """
    response = Mock(spec=httpx.Response)
    response.status_code = 404
    response.headers = {}
    response.json.return_value = {"detail": "Resource not found"}
    return response


@pytest.fixture
def mock_error_response_500() -> Mock:
    """Fixture providing a mocked 500 Internal Server Error response.
    
    Returns:
        Mock httpx.Response with 500 status and server error.
    """
    response = Mock(spec=httpx.Response)
    response.status_code = 500
    response.headers = {}
    response.json.return_value = {"detail": "Internal server error"}
    return response

