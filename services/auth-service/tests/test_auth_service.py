"""
Tests unitarios para el servicio de autenticación.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.auth_service import login, signup, authenticate_user
from app.schemas.user import LoginRequest, UserCreate
from app.database.models import User
from app.exceptions.domain import (
    UserNotFoundError,
    InvalidPasswordError,
    UserAlreadyExistsError,
    DatabaseError,
)


class TestAuthenticateUser:
    """Tests for the authenticate_user function."""

    @patch("app.services.auth_service.user_service.get_user_by_email")
    @patch("app.services.auth_service.passwords.verify_password")
    def test_authenticate_user_success(
        self, mock_verify: Mock, mock_get_user: Mock, mock_db: Session
    ) -> None:
        """
        Test del happy path: autenticación exitosa de usuario.
        Arrange: Mock de usuario y verificación de contraseña exitosa
        Act: Autenticar usuario con credenciales correctas
        Assert: Debe retornar el usuario correcto
        """
        mock_user = Mock(spec=User)
        mock_user.password = "hashed_password"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = True

        result = authenticate_user("test@example.com", "password123", mock_db)

        assert result == mock_user
        mock_get_user.assert_called_once_with("test@example.com", mock_db)
        mock_verify.assert_called_once_with("password123", "hashed_password")

    @patch("app.services.auth_service.user_service.get_user_by_email")
    def test_authenticate_user_not_found(
        self, mock_get_user: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: autenticación con usuario inexistente.
        Arrange: Mock que lanza UserNotFoundError
        Act: Autenticar usuario que no existe
        Assert: Debe lanzar UserNotFoundError
        """
        mock_get_user.side_effect = UserNotFoundError("User not found")

        with pytest.raises(UserNotFoundError) as exc_info:
            authenticate_user("test@example.com", "password123", mock_db)

        assert "not found" in str(exc_info.value).lower()
        mock_get_user.assert_called_once_with("test@example.com", mock_db)

    @patch("app.services.auth_service.user_service.get_user_by_email")
    @patch("app.services.auth_service.passwords.verify_password")
    def test_authenticate_user_invalid_password(
        self, mock_verify: Mock, mock_get_user: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: autenticación con contraseña incorrecta.
        Arrange: Mock de usuario y verificación de contraseña fallida
        Act: Autenticar usuario con contraseña incorrecta
        Assert: Debe lanzar InvalidPasswordError
        """
        mock_user = Mock(spec=User)
        mock_user.password = "hashed_password"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False

        with pytest.raises(InvalidPasswordError) as exc_info:
            authenticate_user("test@example.com", "wrong_password", mock_db)

        assert (
            "password" in str(exc_info.value).lower()
            or "incorrect" in str(exc_info.value).lower()
        )
        mock_verify.assert_called_once_with("wrong_password", "hashed_password")


class TestLogin:
    """Tests for the login function."""

    @patch("app.services.auth_service.authenticate_user")
    @patch("app.services.auth_service.tokens.create_access_token")
    def test_login_success(
        self, mock_create_token: Mock, mock_authenticate: Mock, mock_db: Session
    ) -> None:
        """
        Test del happy path: login exitoso.
        Arrange: Mock de usuario y token
        Act: Hacer login con credenciales válidas
        Assert: Debe retornar tupla (usuario, token) correcta
        """
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime.now()
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "test_token"

        login_data = LoginRequest(email="test@example.com", password="password123")
        result: Tuple[User, str] = login(login_data, mock_db)

        user, token = result
        assert user == mock_user
        assert token == "test_token"
        mock_create_token.assert_called_once_with(data={"sub": "testuser"})

    @patch("app.services.auth_service.authenticate_user")
    def test_login_invalid_credentials(
        self, mock_authenticate: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: login con credenciales inválidas (usuario no encontrado).
        Arrange: Mock que lanza UserNotFoundError
        Act: Hacer login con email inexistente
        Assert: Debe lanzar HTTPException con código 401
        """
        mock_authenticate.side_effect = UserNotFoundError("User not found")
        login_data = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(HTTPException) as exc_info:
            login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            "incorrect" in str(exc_info.value.detail).lower()
            or "password" in str(exc_info.value.detail).lower()
        )

    @patch("app.services.auth_service.authenticate_user")
    def test_login_invalid_password(
        self, mock_authenticate: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: login con contraseña incorrecta.
        Arrange: Mock que lanza InvalidPasswordError
        Act: Hacer login con contraseña incorrecta
        Assert: Debe lanzar HTTPException con código 401
        """
        mock_authenticate.side_effect = InvalidPasswordError("Incorrect password")
        login_data = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(HTTPException) as exc_info:
            login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            "incorrect" in str(exc_info.value.detail).lower()
            or "password" in str(exc_info.value.detail).lower()
        )

    @patch("app.services.auth_service.authenticate_user")
    @patch("app.services.auth_service.tokens.create_access_token")
    def test_login_server_error(
        self, mock_create_token: Mock, mock_authenticate: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: error de servidor durante login.
        Arrange: Mock que lanza excepción genérica
        Act: Hacer login
        Assert: Debe lanzar HTTPException con código 500
        """
        mock_authenticate.side_effect = Exception("Database connection error")
        login_data = LoginRequest(email="test@example.com", password="password123")

        with pytest.raises(HTTPException) as exc_info:
            login(login_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in str(exc_info.value.detail).lower()


class TestSignup:
    """Tests for the signup function."""

    @patch("app.services.auth_service.user_service.create_user")
    @patch("app.services.auth_service.passwords.get_password_hash")
    def test_signup_success(
        self, mock_hash: Mock, mock_create: Mock, mock_db: Session
    ) -> None:
        """
        Test del happy path: registro exitoso de usuario.
        Arrange: Mock de hash y creación de usuario
        Act: Registrar nuevo usuario
        Assert: Debe retornar el usuario creado
        """
        mock_hash.return_value = "hashed_password"
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"
        mock_user.created_at = datetime.now()
        mock_create.return_value = mock_user

        user_data = UserCreate(
            username="newuser", email="new@example.com", password="password123"
        )
        result = signup(user_data, mock_db)

        assert result == mock_user
        mock_hash.assert_called_once_with("password123")
        mock_create.assert_called_once_with(
            email="new@example.com",
            username="newuser",
            hashed_password="hashed_password",
            db=mock_db,
        )

    @patch("app.services.auth_service.user_service.create_user")
    @patch("app.services.auth_service.passwords.get_password_hash")
    def test_signup_user_already_exists(
        self, mock_hash: Mock, mock_create: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: registro con email o username duplicado.
        Arrange: Mock que lanza UserAlreadyExistsError
        Act: Registrar usuario con email/username existente
        Assert: Debe lanzar HTTPException con código 409
        """
        mock_hash.return_value = "hashed_password"
        mock_create.side_effect = UserAlreadyExistsError(
            "User with email existing@example.com or username existinguser already exists"
        )

        user_data = UserCreate(
            username="existinguser",
            email="existing@example.com",
            password="password123",
        )

        with pytest.raises(HTTPException) as exc_info:
            signup(user_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert (
            "already exists" in str(exc_info.value.detail).lower()
            or "exists" in str(exc_info.value.detail).lower()
        )

    @patch("app.services.auth_service.user_service.create_user")
    @patch("app.services.auth_service.passwords.get_password_hash")
    def test_signup_database_error(
        self, mock_hash: Mock, mock_create: Mock, mock_db: Session
    ) -> None:
        """
        Test de error: error de base de datos durante registro.
        Arrange: Mock que lanza DatabaseError
        Act: Registrar usuario
        Assert: Debe lanzar HTTPException con código 500
        """
        mock_hash.return_value = "hashed_password"
        mock_create.side_effect = DatabaseError("Database connection lost")

        user_data = UserCreate(
            username="newuser", email="new@example.com", password="password123"
        )

        with pytest.raises(HTTPException) as exc_info:
            signup(user_data, mock_db)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "database" in str(exc_info.value.detail).lower()
            or "error" in str(exc_info.value.detail).lower()
        )
