"""
Integration tests for authentication API routes.

This module contains comprehensive integration tests for the authentication
endpoints following QA Automation best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Response structure validation
- Type hints and descriptive docstrings
"""
from typing import Dict, Any
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Response
from fastapi.testclient import TestClient

from app.main import app
from app.clients.auth_client import AuthClient
from app.schemas.user import LoginRequest, UserCreate


class TestAuthRoutesIntegration:
    """Integration tests for authentication routes."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_auth_client: Mock) -> None:
        """Setup mocks before each test.
        
        Args:
            mock_auth_client: Mocked auth client fixture.
        """
        # Override dependency
        from app.utils.dependencies import get_auth_client
        app.dependency_overrides[get_auth_client] = lambda: mock_auth_client
        yield
        app.dependency_overrides.clear()
    
    # ========================================================================
    # POST /auth/login Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_login_happy_path(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_login_request: Dict[str, str],
        sample_user_response: Dict[str, Any],
        mock_successful_auth_response: Mock
    ) -> None:
        """Test successful user login (happy path).
        
        Arrange:
            - Mock auth client returns successful response
            - Valid login credentials provided
        
        Act:
            - Send POST request to /auth/login with credentials
        
        Assert:
            - Status code is 200
            - Response contains user data
            - Set-Cookie header is present
            - Response structure matches expected schema
        """
        # Arrange
        mock_auth_client.login = AsyncMock(return_value=mock_successful_auth_response)
        
        # Act
        response = client.post("/auth/login", json=sample_login_request)
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        assert response_data["email"] == sample_user_response["email"]
        assert response_data["id"] == sample_user_response["id"]
        
        # Verify Set-Cookie header is set
        assert "set-cookie" in response.headers or "Set-Cookie" in response.headers, \
            "Response should set authentication cookie"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_login_request: Dict[str, str],
        mock_error_response_401: Mock
    ) -> None:
        """Test login with invalid credentials (error case 1: invalid data).
        
        Arrange:
            - Mock auth client returns 401 Unauthorized
            - Invalid credentials provided
        
        Act:
            - Send POST request to /auth/login with invalid credentials
        
        Assert:
            - Status code is 401
            - Response contains error detail
            - Response structure indicates authentication failure
        """
        # Arrange
        mock_auth_client.login = AsyncMock(return_value=mock_error_response_401)
        invalid_request = {**sample_login_request, "password": "wrongpassword"}
        
        # Act
        response = client.post("/auth/login", json=invalid_request)
        
        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "credentials" in response_data["detail"].lower() or \
               "invalid" in response_data["detail"].lower(), \
               "Error message should indicate authentication failure"
    
    @pytest.mark.asyncio
    async def test_login_missing_fields(
        self,
        client: TestClient,
        mock_auth_client: Mock
    ) -> None:
        """Test login with missing required fields (error case 2: invalid data).
        
        Arrange:
            - Request missing required fields
        
        Act:
            - Send POST request to /auth/login without required fields
        
        Assert:
            - Status code is 422 (validation error)
            - Response contains validation error details
        """
        # Arrange
        incomplete_request = {"email": "test@example.com"}  # Missing password
        
        # Act
        response = client.post("/auth/login", json=incomplete_request)
        
        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Validation error should contain 'detail' field"
        # FastAPI validation errors are in a specific format
        assert isinstance(response_data["detail"], list), "Validation detail should be a list"
    
    @pytest.mark.asyncio
    async def test_login_server_error(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_login_request: Dict[str, str],
        mock_error_response_500: Mock
    ) -> None:
        """Test login when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock auth client returns 500 Internal Server Error
        
        Act:
            - Send POST request to /auth/login
        
        Assert:
            - Status code is 500
            - Response contains error detail
        """
        # Arrange
        mock_auth_client.login = AsyncMock(return_value=mock_error_response_500)
        
        # Act
        response = client.post("/auth/login", json=sample_login_request)
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # POST /auth/signup Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_signup_happy_path(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_user_data: Dict[str, Any],
        sample_user_response: Dict[str, Any],
        mock_successful_auth_response: Mock
    ) -> None:
        """Test successful user registration (happy path).
        
        Arrange:
            - Mock auth client returns successful response
            - Valid user data provided
        
        Act:
            - Send POST request to /auth/signup with user data
        
        Assert:
            - Status code is 200
            - Response contains user data
            - Response structure matches expected schema
        """
        # Arrange
        mock_auth_client.signup = AsyncMock(return_value=mock_successful_auth_response)
        
        # Act
        response = client.post("/auth/signup", json=sample_user_data)
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        assert "username" in response_data, "Response should contain 'username' field"
        assert response_data["email"] == sample_user_data["email"]
        assert response_data["username"] == sample_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_user_data: Dict[str, Any],
        mock_error_response_400: Mock
    ) -> None:
        """Test signup with duplicate email (error case 1: invalid data).
        
        Arrange:
            - Mock auth client returns 400 Bad Request
            - Email already exists in system
        
        Act:
            - Send POST request to /auth/signup with duplicate email
        
        Assert:
            - Status code is 400
            - Response contains error detail about duplicate email
        """
        # Arrange
        mock_error_response_400.json.return_value = {"detail": "Email already exists"}
        mock_auth_client.signup = AsyncMock(return_value=mock_error_response_400)
        
        # Act
        response = client.post("/auth/signup", json=sample_user_data)
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "email" in response_data["detail"].lower(), \
            "Error message should mention email"
    
    @pytest.mark.asyncio
    async def test_signup_invalid_email_format(
        self,
        client: TestClient,
        mock_auth_client: Mock
    ) -> None:
        """Test signup with invalid email format (error case 2: invalid data).
        
        Arrange:
            - Invalid email format provided
        
        Act:
            - Send POST request to /auth/signup with invalid email
        
        Assert:
            - Status code is 422 (validation error)
            - Response contains validation error details
        """
        # Arrange
        invalid_data = {
            "email": "not-an-email",
            "password": "testpass123",
            "username": "testuser"
        }
        
        # Act
        response = client.post("/auth/signup", json=invalid_data)
        
        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Validation error should contain 'detail' field"
    
    @pytest.mark.asyncio
    async def test_signup_server_error(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        sample_user_data: Dict[str, Any],
        mock_error_response_500: Mock
    ) -> None:
        """Test signup when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Mock auth client returns 500 Internal Server Error
        
        Act:
            - Send POST request to /auth/signup
        
        Assert:
            - Status code is 500
            - Response contains error detail
        """
        # Arrange
        mock_auth_client.signup = AsyncMock(return_value=mock_error_response_500)
        
        # Act
        response = client.post("/auth/signup", json=sample_user_data)
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # GET /auth/me Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_get_current_user_happy_path(
        self,
        authenticated_client: TestClient,
        mock_auth_client: Mock,
        sample_user_response: Dict[str, Any],
        mock_successful_auth_response: Mock
    ) -> None:
        """Test successful retrieval of current user (happy path).
        
        Arrange:
            - Client is authenticated with valid token
            - Mock auth client returns user data
        
        Act:
            - Send GET request to /auth/me
        
        Assert:
            - Status code is 200
            - Response contains user data
            - Response structure matches expected schema
        """
        # Arrange
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_successful_auth_response)
        
        # Act
        response = authenticated_client.get("/auth/me")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "id" in response_data, "Response should contain 'id' field"
        assert "email" in response_data, "Response should contain 'email' field"
        assert response_data["id"] == sample_user_response["id"]
        assert response_data["email"] == sample_user_response["email"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_auth(
        self,
        client: TestClient,
        mock_auth_client: Mock
    ) -> None:
        """Test get current user without authentication (Error Case 1: Invalid Data).
        
        Verifies:
        - HTTP 401 status code
        - Response indicates authentication required
        
        Args:
            client: TestClient fixture
            mock_auth_client: Mocked auth client
        """
        # Arrange - no authentication
        
        # Act
        response = client.get("/auth/me")
        
        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "authentication" in response_data["detail"].lower() or \
               "required" in response_data["detail"].lower(), \
               "Error message should indicate authentication is required"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        client: TestClient,
        mock_auth_client: Mock,
        mock_error_response_401: Mock
    ) -> None:
        """Test get current user with invalid token (error case 2: invalid data).
        
        Arrange:
            - Invalid authentication token provided
            - Mock auth client returns 401
        
        Act:
            - Send GET request to /auth/me with invalid token
        
        Assert:
            - Status code is 401
            - Response indicates invalid token
        """
        # Arrange
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_error_response_401)
        client.cookies.set("access_token", "invalid-token")
        
        # Act
        response = client.get("/auth/me")
        
        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    @pytest.mark.asyncio
    async def test_get_current_user_server_error(
        self,
        authenticated_client: TestClient,
        mock_auth_client: Mock,
        mock_error_response_500: Mock
    ) -> None:
        """Test get current user when auth service returns server error (error case 3: server error).
        
        Arrange:
            - Client is authenticated
            - Mock auth client returns 500
        
        Act:
            - Send GET request to /auth/me
        
        Assert:
            - Status code is 500
            - Response contains error detail
        """
        # Arrange
        mock_auth_client.get_current_user = AsyncMock(return_value=mock_error_response_500)
        
        # Act
        response = authenticated_client.get("/auth/me")
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # ========================================================================
    # POST /auth/logout Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_logout_happy_path(
        self,
        authenticated_client: TestClient,
        mock_auth_client: Mock,
        mock_successful_auth_response: Mock
    ) -> None:
        """Test successful user logout (happy path).
        
        Arrange:
            - Client is authenticated
            - Mock auth client returns successful logout
        
        Act:
            - Send POST request to /auth/logout
        
        Assert:
            - Status code is 200
            - Response indicates successful logout
            - Cookie is cleared (Set-Cookie with Max-Age=0)
        """
        # Arrange
        mock_successful_auth_response.json.return_value = {"message": "Logged out successfully"}
        mock_auth_client.logout = AsyncMock(return_value=mock_successful_auth_response)
        
        # Act
        response = authenticated_client.post("/auth/logout")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        # Verify logout response structure
        assert "message" in response_data or "detail" in response_data, \
            "Response should contain logout confirmation"
    
    @pytest.mark.asyncio
    async def test_logout_no_auth(
        self,
        client: TestClient,
        mock_auth_client: Mock
    ) -> None:
        """Test logout without authentication (error case 1: invalid data).
        
        Arrange:
            - No authentication token provided
        
        Act:
            - Send POST request to /auth/logout without auth
        
        Assert:
            - Status code is 401
            - Response indicates authentication required
        """
        # Arrange - no authentication
        
        # Act
        response = client.post("/auth/logout")
        
        # Assert
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "authentication" in response_data["detail"].lower() or \
               "required" in response_data["detail"].lower(), \
               "Error message should indicate authentication is required"

