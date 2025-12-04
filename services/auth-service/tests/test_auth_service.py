"""
Unit tests for authentication service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.auth_service import login, signup, authenticate_user
from app.schemas.user import LoginRequest, UserCreate
from app.database.models import User
from app.exceptions.domain import UserNotFoundError, InvalidPasswordError, UserAlreadyExistsError


class TestAuthenticateUser:
    """Tests for authenticate_user function."""
    
    @patch('app.services.auth_service.user_service.get_user_by_email')
    @patch('app.services.auth_service.passwords.verify_password')
    def test_authenticate_user_success(self, mock_verify, mock_get_user):
        """Test successful user authentication."""
        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.password = "hashed_password"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = True
        
        # Test
        db = Mock(spec=Session)
        result = authenticate_user("test@example.com", "password123", db)
        
        # Assertions
        assert result == mock_user
        mock_get_user.assert_called_once_with("test@example.com", db)
        mock_verify.assert_called_once_with("password123", "hashed_password")
    
    @patch('app.services.auth_service.user_service.get_user_by_email')
    def test_authenticate_user_not_found(self, mock_get_user):
        """Test authentication with non-existent user."""
        mock_get_user.side_effect = UserNotFoundError("User not found")
        db = Mock(spec=Session)
        
        with pytest.raises(UserNotFoundError):
            authenticate_user("test@example.com", "password123", db)
    
    @patch('app.services.auth_service.user_service.get_user_by_email')
    @patch('app.services.auth_service.passwords.verify_password')
    def test_authenticate_user_invalid_password(self, mock_verify, mock_get_user):
        """Test authentication with incorrect password."""
        mock_user = Mock(spec=User)
        mock_user.password = "hashed_password"
        mock_get_user.return_value = mock_user
        mock_verify.return_value = False
        
        db = Mock(spec=Session)
        with pytest.raises(InvalidPasswordError):
            authenticate_user("test@example.com", "wrong_password", db)


class TestLogin:
    """Tests for login function."""
    
    @patch('app.services.auth_service.authenticate_user')
    @patch('app.services.auth_service.tokens.create_access_token')
    def test_login_success(self, mock_create_token, mock_authenticate):
        """Test successful login."""
        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime.now()  # Add valid datetime for Pydantic validation
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "test_token"
        
        # Test
        db = Mock(spec=Session)
        login_data = LoginRequest(email="test@example.com", password="password123")
        result = login(login_data, db)
        
        # Assertions
        assert result.access_token == "test_token"
        assert result.token_type == "bearer"
        assert result.user.id == mock_user.id
        assert result.user.username == mock_user.username
        assert result.user.email == mock_user.email
        mock_create_token.assert_called_once_with(data={"sub": "testuser"})
    
    @patch('app.services.auth_service.authenticate_user')
    def test_login_invalid_credentials(self, mock_authenticate):
        """Test login with invalid credentials."""
        mock_authenticate.side_effect = UserNotFoundError("User not found")
        db = Mock(spec=Session)
        login_data = LoginRequest(email="test@example.com", password="wrong_password")
        
        with pytest.raises(HTTPException) as exc_info:
            login(login_data, db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in str(exc_info.value.detail)
    
    @patch('app.services.auth_service.authenticate_user')
    def test_login_invalid_password(self, mock_authenticate):
        """Test login with incorrect password."""
        mock_authenticate.side_effect = InvalidPasswordError("Incorrect password")
        db = Mock(spec=Session)
        login_data = LoginRequest(email="test@example.com", password="wrong_password")
        
        with pytest.raises(HTTPException) as exc_info:
            login(login_data, db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestSignup:
    """Tests for signup function."""
    
    @patch('app.services.auth_service.user_service.create_user')
    @patch('app.services.auth_service.passwords.get_password_hash')
    def test_signup_success(self, mock_hash, mock_create):
        """Test successful user signup."""
        # Setup mocks
        mock_hash.return_value = "hashed_password"
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"
        mock_user.created_at = datetime.now()
        mock_create.return_value = mock_user
        
        # Test
        db = Mock(spec=Session)
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123"
        )
        result = signup(user_data, db)
        
        # Assertions
        assert result == mock_user
        mock_hash.assert_called_once_with("password123")
        mock_create.assert_called_once_with(
            email="new@example.com",
            username="newuser",
            hashed_password="hashed_password",
            db=db
        )
    
    @patch('app.services.auth_service.user_service.create_user')
    @patch('app.services.auth_service.passwords.get_password_hash')
    def test_signup_user_already_exists(self, mock_hash, mock_create):
        """Test signup with existing email."""
        # Setup mocks
        mock_hash.return_value = "hashed_password"
        mock_create.side_effect = UserAlreadyExistsError("User with email existing@example.com or username existinguser already exists")
        
        db = Mock(spec=Session)
        user_data = UserCreate(
            username="existinguser",
            email="existing@example.com",
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            signup(user_data, db)
        
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in str(exc_info.value.detail)

