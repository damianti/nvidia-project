"""
Unit tests for AuthClient following QA Automation best practices.

This module contains unit tests with:
- AAA pattern (Arrange, Act, Assert)
- Comprehensive error scenarios
- Response structure validation
- Type hints and descriptive docstrings
"""
from typing import Dict, Any
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.clients.auth_client import AuthClient


class TestAuthClientUnit:
    """Unit tests for AuthClient."""
    
    @pytest.fixture
    def auth_client(self) -> AuthClient:
        """Fixture providing AuthClient instance.
        
        Returns:
            AuthClient instance for testing.
        """
        return AuthClient("http://auth-service:3005")
    
    @pytest.fixture
    def mock_http_client(self) -> AsyncMock:
        """Fixture providing mocked HTTP client.
        
        Returns:
            AsyncMock configured as httpx.AsyncClient.
        """
        return AsyncMock(spec=httpx.AsyncClient)
    
    # ========================================================================
    # Login Method Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_login_happy_path(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test successful login (happy path).
        
        Arrange:
            - Mock HTTP client returns 200 with user data
            - Valid login credentials provided
        
        Act:
            - Call login method with credentials
        
        Assert:
            - Response status code is 200
            - Response contains user data
            - Request was made with correct parameters
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "email": "test@example.com"}
        mock_http_client.request.return_value = mock_response
        
        login_data = {"email": "test@example.com", "password": "password123"}
        
        # Act
        response = await auth_client.login(login_data)
        
        # Assert
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        
        # Verify request parameters
        mock_http_client.request.assert_called_once()
        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/auth/login" in call_kwargs["url"]
        assert call_kwargs["json"] == login_data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test login with invalid credentials (error case 1: invalid data).
        
        Arrange:
            - Mock HTTP client returns 401 Unauthorized
        
        Act:
            - Call login method with invalid credentials
        
        Assert:
            - Response status code is 401
            - Response contains error detail
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid credentials"}
        mock_http_client.request.return_value = mock_response
        
        login_data = {"email": "test@example.com", "password": "wrongpassword"}
        
        # Act
        response = await auth_client.login(login_data)
        
        # Assert
        assert response.status_code == 401, \
            f"Expected status 401, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "invalid" in response_data["detail"].lower() or \
               "credentials" in response_data["detail"].lower(), \
               "Error message should indicate invalid credentials"
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test login with non-existent user (error case 2: resource not found).
        
        Arrange:
            - Mock HTTP client returns 404 Not Found
        
        Act:
            - Call login method with non-existent email
        
        Assert:
            - Response status code is 404
            - Response indicates user not found
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "User not found"}
        mock_http_client.request.return_value = mock_response
        
        login_data = {"email": "nonexistent@example.com", "password": "password123"}
        
        # Act
        response = await auth_client.login(login_data)
        
        # Assert
        assert response.status_code == 404, \
            f"Expected status 404, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "not found" in response_data["detail"].lower(), \
            "Error message should indicate user not found"
    
    @pytest.mark.asyncio
    async def test_login_server_error(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test login when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock HTTP client returns 500 Internal Server Error
        
        Act:
            - Call login method
        
        Assert:
            - Response status code is 500
            - Response contains error detail
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_http_client.request.return_value = mock_response
        
        login_data = {"email": "test@example.com", "password": "password123"}
        
        # Act
        response = await auth_client.login(login_data)
        
        # Assert
        assert response.status_code == 500, \
            f"Expected status 500, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    @pytest.mark.asyncio
    async def test_login_timeout(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test login timeout scenario.
        
        Arrange:
            - Mock HTTP client raises TimeoutException
        
        Act:
            - Call login method
        
        Assert:
            - TimeoutException is raised
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_http_client.request.side_effect = httpx.TimeoutException("Request timeout")
        
        login_data = {"email": "test@example.com", "password": "password123"}
        
        # Act & Assert
        with pytest.raises(httpx.TimeoutException) as exc_info:
            await auth_client.login(login_data)
        
        assert "timeout" in str(exc_info.value).lower(), \
            "Exception should indicate timeout"
    
    # ========================================================================
    # Signup Method Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_signup_happy_path(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test successful user registration (happy path).
        
        Arrange:
            - Mock HTTP client returns 200 with user data
        
        Act:
            - Call signup method with user data
        
        Assert:
            - Response status code is 200
            - Response contains user data with all required fields
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }
        mock_http_client.request.return_value = mock_response
        
        signup_data = {
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser"
        }
        
        # Act
        response = await auth_client.signup(signup_data)
        
        # Assert
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        assert "username" in response_data, "Response should contain 'username' field"
        assert response_data["email"] == signup_data["email"]
        assert response_data["username"] == signup_data["username"]
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test signup with duplicate email (error case 1: invalid data).
        
        Arrange:
            - Mock HTTP client returns 400 Bad Request
        
        Act:
            - Call signup method with existing email
        
        Assert:
            - Response status code is 400
            - Response indicates email already exists
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Email already exists"}
        mock_http_client.request.return_value = mock_response
        
        signup_data = {
            "email": "existing@example.com",
            "password": "password123",
            "username": "testuser"
        }
        
        # Act
        response = await auth_client.signup(signup_data)
        
        # Assert
        assert response.status_code == 400, \
            f"Expected status 400, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "email" in response_data["detail"].lower(), \
            "Error message should mention email"
    
    @pytest.mark.asyncio
    async def test_signup_server_error(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test signup when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock HTTP client returns 500 Internal Server Error
        
        Act:
            - Call signup method
        
        Assert:
            - Response status code is 500
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_http_client.request.return_value = mock_response
        
        signup_data = {
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser"
        }
        
        # Act
        response = await auth_client.signup(signup_data)
        
        # Assert
        assert response.status_code == 500, \
            f"Expected status 500, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # Get Current User Method Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_get_current_user_happy_path(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test successful get current user (happy path).
        
        Arrange:
            - Mock HTTP client returns 200 with user data
            - Valid authorization header and cookies provided
        
        Act:
            - Call get_current_user method
        
        Assert:
            - Response status code is 200
            - Response contains user data
            - Request includes authorization header and cookies
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }
        mock_http_client.request.return_value = mock_response
        
        auth_header = "Bearer test-token"
        cookies = {"access_token": "test-token"}
        
        # Act
        response = await auth_client.get_current_user(auth_header, cookies)
        
        # Assert
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        
        # Verify request includes auth header
        call_kwargs = mock_http_client.request.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == auth_header
        assert call_kwargs["cookies"] == cookies
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test get current user with invalid token (error case 1: invalid data).
        
        Arrange:
            - Mock HTTP client returns 401 Unauthorized
        
        Act:
            - Call get_current_user with invalid token
        
        Assert:
            - Response status code is 401
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_http_client.request.return_value = mock_response
        
        # Act
        response = await auth_client.get_current_user("Bearer invalid-token", {})
        
        # Assert
        assert response.status_code == 401, \
            f"Expected status 401, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    @pytest.mark.asyncio
    async def test_get_current_user_server_error(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test get current user when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock HTTP client returns 500 Internal Server Error
        
        Act:
            - Call get_current_user method
        
        Assert:
            - Response status code is 500
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_http_client.request.return_value = mock_response
        
        # Act
        response = await auth_client.get_current_user("Bearer test-token", {})
        
        # Assert
        assert response.status_code == 500, \
            f"Expected status 500, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # Logout Method Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_logout_happy_path(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test successful logout (happy path).
        
        Arrange:
            - Mock HTTP client returns 200 with logout confirmation
        
        Act:
            - Call logout method
        
        Assert:
            - Response status code is 200
            - Response indicates successful logout
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Logged out successfully"}
        mock_http_client.request.return_value = mock_response
        
        # Act
        response = await auth_client.logout("test-token", {"access_token": "test-token"})
        
        # Assert
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "message" in response_data or "detail" in response_data, \
            "Response should contain logout confirmation"
    
    @pytest.mark.asyncio
    async def test_logout_server_error(
        self,
        auth_client: AuthClient,
        mock_http_client: AsyncMock
    ) -> None:
        """Test logout when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock HTTP client returns 500 Internal Server Error
        
        Act:
            - Call logout method
        
        Assert:
            - Response status code is 500
        """
        # Arrange
        auth_client.http_client = mock_http_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_http_client.request.return_value = mock_response
        
        # Act
        response = await auth_client.logout("test-token", {})
        
        # Assert
        assert response.status_code == 500, \
            f"Expected status 500, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # Header Building Tests
    # ========================================================================
    
    def test_build_headers_with_correlation_id(
        self,
        auth_client: AuthClient
    ) -> None:
        """Test building headers with correlation ID.
        
        Arrange:
            - Correlation ID is set in context
        
        Act:
            - Call _build_headers method
        
        Assert:
            - Headers contain X-Correlation-ID
        """
        # Arrange
        with patch("app.clients.auth_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = "test-correlation-id"
            
            # Act
            headers = auth_client._build_headers()
            
            # Assert
            assert isinstance(headers, dict), "Headers should be a dictionary"
            assert "X-Correlation-ID" in headers, \
                "Headers should contain X-Correlation-ID"
            assert headers["X-Correlation-ID"] == "test-correlation-id"
    
    def test_build_headers_without_correlation_id(
        self,
        auth_client: AuthClient
    ) -> None:
        """Test building headers without correlation ID.
        
        Arrange:
            - No correlation ID in context
        
        Act:
            - Call _build_headers method
        
        Assert:
            - Headers are empty dictionary
        """
        # Arrange
        with patch("app.clients.auth_client.correlation_id_var") as mock_var:
            mock_var.get.return_value = None
            
            # Act
            headers = auth_client._build_headers()
            
            # Assert
            assert isinstance(headers, dict), "Headers should be a dictionary"
            assert len(headers) == 0, "Headers should be empty when no correlation ID"

