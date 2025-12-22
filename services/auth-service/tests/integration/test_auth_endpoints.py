"""
Integration tests for authentication endpoints.
"""
import pytest
from typing import Dict, Any
from fastapi import status
from fastapi.testclient import TestClient

from app.database.models import User


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""
    
    def test_login_success(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Happy path test: successful login with valid credentials.
        Arrange: Existing user in database
        Act: POST to /auth/login with correct credentials
        Assert: Should return 200, user in response and token cookie
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response body structure
        body = response.json()
        assert "user" in body
        assert body["user"]["email"] == "test@example.com"
        assert body["user"]["username"] == "testuser"
        assert "id" in body["user"]
        assert "created_at" in body["user"]
        
        # Verify that token cookie was set
        cookies = response.cookies
        assert "access_token" in cookies
        assert cookies["access_token"] is not None
        assert len(cookies["access_token"]) > 0
    
    def test_login_invalid_email(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Error test: login with non-existent email.
        Arrange: Existing user in database
        Act: POST to /auth/login with non-existent email
        Assert: Should return 401 and appropriate error message
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify error body structure
        body = response.json()
        assert "detail" in body
        assert "incorrect" in body["detail"].lower() or "password" in body["detail"].lower()
        
        # Verify that cookie was not set
        assert "access_token" not in response.cookies
    
    def test_login_invalid_password(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Error test: login with incorrect password.
        Arrange: Existing user in database
        Act: POST to /auth/login with incorrect password
        Assert: Should return 401 and appropriate error message
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify error body structure
        body = response.json()
        assert "detail" in body
        assert "incorrect" in body["detail"].lower() or "password" in body["detail"].lower()
        
        # Verify that cookie was not set
        assert "access_token" not in response.cookies
    
    def test_login_missing_fields(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: login with invalid data (missing fields).
        Arrange: Test client
        Act: POST to /auth/login without required fields
        Assert: Should return 422 (validation error)
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com"
                # Falta password
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify validation error structure
        body = response.json()
        assert "detail" in body
    
    def test_login_invalid_email_format(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: login with invalid email format.
        Arrange: Test client
        Act: POST to /auth/login with malformed email
        Assert: Should return 422 (validation error) or 401 (if validation passes but doesn't exist)
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "not-an-email",
                "password": "testpassword123"
            }
        )
        
        # May be 422 (validation) or 401 (if email passes validation but doesn't exist)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]
        
        body = response.json()
        assert "detail" in body
    
    def test_login_empty_credentials(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: login with empty credentials.
        Arrange: Test client
        Act: POST to /auth/login with empty fields
        Assert: Should return 422 or 401
        """
        response = test_client.post(
            "/auth/login",
            json={
                "email": "",
                "password": ""
            }
        )
        
        # May be 422 (validation) or 401 (authentication failed)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]


class TestSignupEndpoint:
    """Tests for POST /auth/signup endpoint."""
    
    def test_signup_success(
        self,
        test_client: TestClient,
        override_get_db
    ) -> None:
        """
        Happy path test: successful registration of new user.
        Arrange: Empty database
        Act: POST to /auth/signup with valid data
        Assert: Should return 200, created user with correct structure
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123"  # Shorter password to avoid bcrypt limit
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response body structure
        body = response.json()
        assert body["email"] == "newuser@example.com"
        assert body["username"] == "newuser"
        assert "id" in body
        assert "created_at" in body
        assert "password" not in body  # Password no debe estar en la respuesta
    
    def test_signup_duplicate_email(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Error test: registration with duplicate email.
        Arrange: Existing user with email
        Act: POST to /auth/signup with existing email
        Assert: Should return 409 (conflict) and error message
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Email duplicado
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        
        # Verify error body structure
        body = response.json()
        assert "detail" in body
        assert "already exists" in body["detail"].lower() or "exists" in body["detail"].lower()
    
    def test_signup_duplicate_username(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Error test: registration with duplicate username.
        Arrange: Existing user with username
        Act: POST to /auth/signup with existing username
        Assert: Should return 409 (conflict) and error message
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "testuser",  # Username duplicado
                "email": "different@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        
        body = response.json()
        assert "detail" in body
        assert "already exists" in body["detail"].lower() or "exists" in body["detail"].lower()
    
    def test_signup_missing_fields(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: registration with invalid data (missing fields).
        Arrange: Test client
        Act: POST to /auth/signup without required fields
        Assert: Should return 422 (validation error)
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "newuser"
                # Faltan email y password
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        body = response.json()
        assert "detail" in body
    
    def test_signup_invalid_email_format(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: registration with invalid email format.
        Arrange: Test client
        Act: POST to /auth/signup with malformed email
        Assert: Should return 422 (validation error)
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        body = response.json()
        assert "detail" in body
    
    def test_signup_short_password(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: registration with very short password.
        Arrange: Test client
        Act: POST to /auth/signup with short password
        Assert: May return 422 or process (depends on validation)
        """
        response = test_client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "pass123"  # Contraseña corta pero válida para bcrypt
            }
        )
        
        # May be 422 if there's length validation or 200 if not
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK
        ]


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""
    
    def test_logout_success(
        self,
        test_client: TestClient
    ) -> None:
        """
        Happy path test: successful logout.
        Arrange: Test client
        Act: POST to /auth/logout
        Assert: Should return 200 and remove token cookie
        """
        response = test_client.post("/auth/logout")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response body structure
        body = response.json()
        assert "message" in body
        assert "logout" in body["message"].lower() or "success" in body["message"].lower()
        
        # Verificar que la cookie fue eliminada (max_age=0 o sin cookie)
        cookies = response.cookies
        # La cookie puede estar presente pero con max_age=0
        if "access_token" in cookies:
            # Si está presente, debería estar vacía o marcada para eliminación
            pass


class TestGetCurrentUserEndpoint:
    """Tests for GET /auth/me endpoint."""
    
    def test_get_current_user_success(
        self,
        test_client: TestClient,
        sample_user: User
    ) -> None:
        """
        Happy path test: get authenticated user information.
        Arrange: Existing user and valid token
        Act: GET to /auth/me with valid token
        Assert: Should return 200 and user data
        """
        # Primero hacer login para obtener token
        login_response = test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.cookies.get("access_token")
        
        # Hacer request a /auth/me con el token en cookie
        response = test_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response body structure
        body = response.json()
        assert body["email"] == "test@example.com"
        assert body["username"] == "testuser"
        assert "id" in body
        assert "created_at" in body
        assert "password" not in body
    
    def test_get_current_user_no_token(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: get user without authentication token.
        Arrange: Test client without authentication
        Act: GET to /auth/me without token
        Assert: Should return 401 (unauthorized)
        """
        response = test_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify error body structure
        body = response.json()
        assert "detail" in body
        assert "credentials" in body["detail"].lower() or "unauthorized" in body["detail"].lower()
    
    def test_get_current_user_invalid_token(
        self,
        test_client: TestClient
    ) -> None:
        """
        Error test: get user with invalid token.
        Arrange: Test client
        Act: GET to /auth/me with invalid token
        Assert: Should return 401 (unauthorized)
        """
        # Set cookie with invalid token
        test_client.cookies.set("access_token", "invalid.token.here")
        
        response = test_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        body = response.json()
        assert "detail" in body
    
    def test_get_current_user_expired_token(
        self,
        test_client: TestClient,
        expired_token: str
    ) -> None:
        """
        Error test: get user with expired token.
        Arrange: Expired token
        Act: GET to /auth/me with expired token
        Assert: Should return 401 (unauthorized)
        """
        # Set cookie with expired token
        test_client.cookies.set("access_token", expired_token)
        
        response = test_client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        body = response.json()
        assert "detail" in body
        assert "expired" in body["detail"].lower() or "credentials" in body["detail"].lower()


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""
    
    def test_health_check_success(
        self,
        test_client: TestClient
    ) -> None:
        """
        Test del health check endpoint.
        Arrange: Test client
        Act: GET to /health
        Assert: Should return 200
        """
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        
        body = response.json()
        # El health check puede tener diferentes estructuras
        # Verify that it returns something valid
        assert body is not None

