"""
Tests unitarios para el servicio de usuarios.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import EmailStr

from app.services import user_service
from app.database.models import User
from app.exceptions.domain import (
    UserNotFoundError,
    UserAlreadyExistsError,
    DatabaseError
)


class TestGetUserByEmail:
    """Tests para obtener usuario por email."""
    
    @patch('app.services.user_service.user_repository.get_user_by_email')
    def test_get_user_by_email_success(
        self,
        mock_get_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica la obtención exitosa de un usuario por email.
        Arrange: Mock de usuario existente
        Act: Obtener usuario por email
        Assert: Debe retornar el usuario correcto
        """
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        result = user_service.get_user_by_email("test@example.com", mock_db)
        
        assert result == mock_user
        mock_get_user.assert_called_once_with("test@example.com", mock_db)
    
    @patch('app.services.user_service.user_repository.get_user_by_email')
    def test_get_user_by_email_not_found(
        self,
        mock_get_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica que se lanza excepción cuando el usuario no existe.
        Arrange: Mock que retorna None
        Act: Obtener usuario por email inexistente
        Assert: Debe lanzar UserNotFoundError
        """
        mock_get_user.return_value = None
        
        with pytest.raises(UserNotFoundError) as exc_info:
            user_service.get_user_by_email("nonexistent@example.com", mock_db)
        
        assert "not found" in str(exc_info.value).lower()
        mock_get_user.assert_called_once_with("nonexistent@example.com", mock_db)


class TestGetUserByUsername:
    """Tests para obtener usuario por username."""
    
    @patch('app.services.user_service.user_repository.get_user_by_username')
    def test_get_user_by_username_success(
        self,
        mock_get_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica la obtención exitosa de un usuario por username.
        Arrange: Mock de usuario existente
        Act: Obtener usuario por username
        Assert: Debe retornar el usuario correcto
        """
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_get_user.return_value = mock_user
        
        result = user_service.get_user_by_username("testuser", mock_db)
        
        assert result == mock_user
        mock_get_user.assert_called_once_with("testuser", mock_db)
    
    @patch('app.services.user_service.user_repository.get_user_by_username')
    def test_get_user_by_username_not_found(
        self,
        mock_get_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica que se lanza excepción cuando el usuario no existe.
        Arrange: Mock que retorna None
        Act: Obtener usuario por username inexistente
        Assert: Debe lanzar UserNotFoundError
        """
        mock_get_user.return_value = None
        
        with pytest.raises(UserNotFoundError) as exc_info:
            user_service.get_user_by_username("nonexistent", mock_db)
        
        assert "not found" in str(exc_info.value).lower()
        mock_get_user.assert_called_once_with("nonexistent", mock_db)


class TestCreateUser:
    """Tests para la creación de usuarios."""
    
    @patch('app.services.user_service.user_repository.create_user')
    def test_create_user_success(
        self,
        mock_create_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica la creación exitosa de un usuario.
        Arrange: Mock de usuario creado
        Act: Crear usuario
        Assert: Debe retornar el usuario creado y hacer commit
        """
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_create_user.return_value = mock_user
        
        result = user_service.create_user(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            db=mock_db
        )
        
        assert result == mock_user
        mock_create_user.assert_called_once_with(
            "test@example.com",
            "testuser",
            "hashed_password",
            mock_db
        )
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @patch('app.services.user_service.user_repository.create_user')
    def test_create_user_integrity_error_email_exists(
        self,
        mock_create_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica que se lanza excepción cuando el email ya existe.
        Arrange: Mock que lanza IntegrityError
        Act: Crear usuario con email duplicado
        Assert: Debe lanzar UserAlreadyExistsError y hacer rollback
        """
        mock_create_user.side_effect = IntegrityError(
            statement="INSERT INTO users",
            params={},
            orig=Exception("UNIQUE constraint failed: users.email")
        )
        
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            user_service.create_user(
                email="existing@example.com",
                username="testuser",
                hashed_password="hashed_password",
                db=mock_db
            )
        
        assert "already exists" in str(exc_info.value).lower()
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()
    
    @patch('app.services.user_service.user_repository.create_user')
    def test_create_user_integrity_error_username_exists(
        self,
        mock_create_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica que se lanza excepción cuando el username ya existe.
        Arrange: Mock que lanza IntegrityError
        Act: Crear usuario con username duplicado
        Assert: Debe lanzar UserAlreadyExistsError y hacer rollback
        """
        mock_create_user.side_effect = IntegrityError(
            statement="INSERT INTO users",
            params={},
            orig=Exception("UNIQUE constraint failed: users.username")
        )
        
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            user_service.create_user(
                email="test@example.com",
                username="existinguser",
                hashed_password="hashed_password",
                db=mock_db
            )
        
        assert "already exists" in str(exc_info.value).lower()
        mock_db.rollback.assert_called_once()
    
    @patch('app.services.user_service.user_repository.create_user')
    def test_create_user_database_error(
        self,
        mock_create_user: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica el manejo de errores de base de datos.
        Arrange: Mock que lanza SQLAlchemyError
        Act: Crear usuario
        Assert: Debe lanzar DatabaseError y hacer rollback
        """
        mock_create_user.side_effect = SQLAlchemyError("Database connection lost")
        
        with pytest.raises(DatabaseError) as exc_info:
            user_service.create_user(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                db=mock_db
            )
        
        assert "database error" in str(exc_info.value).lower()
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


class TestCountUsers:
    """Tests para contar usuarios."""
    
    @patch('app.services.user_service.user_repository.count_users')
    def test_count_users_success(
        self,
        mock_count: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica el conteo correcto de usuarios.
        Arrange: Mock que retorna un número
        Act: Contar usuarios
        Assert: Debe retornar el número correcto
        """
        mock_count.return_value = 5
        
        result = user_service.count_users(mock_db)
        
        assert result == 5
        mock_count.assert_called_once_with(mock_db)
    
    @patch('app.services.user_service.user_repository.count_users')
    def test_count_users_zero(
        self,
        mock_count: Mock,
        mock_db: Session
    ) -> None:
        """
        Test que verifica el conteo cuando no hay usuarios.
        Arrange: Mock que retorna 0
        Act: Contar usuarios
        Assert: Debe retornar 0
        """
        mock_count.return_value = 0
        
        result = user_service.count_users(mock_db)
        
        assert result == 0
        mock_count.assert_called_once_with(mock_db)

