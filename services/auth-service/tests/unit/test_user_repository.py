"""
Unit tests for the user repository.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories import user_repository
from app.database.models import User


class TestGetUserByEmail:
    """Tests for getting user by email from repository."""

    @patch("app.utils.passwords.pwd_context")
    def test_get_user_by_email_exists(
        self, mock_pwd_context: MagicMock, db_session: Session
    ) -> None:
        """
        Test that verifies getting an existing user by email.
        Arrange: User created in database with mocked hash
        Act: Get user by email
        Assert: Should return the correct user
        """
        from app.utils import passwords

        mock_hash = (
            "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        )
        mock_pwd_context.hash.return_value = mock_hash

        user = User(
            username="testuser",
            email="test@example.com",
            password=passwords.get_password_hash("password123"),
            created_at=datetime.now(),
        )
        db_session.add(user)
        db_session.commit()

        result = user_repository.get_user_by_email("test@example.com", db_session)

        assert result is not None
        assert result.email == "test@example.com"
        assert result.username == "testuser"

    def test_get_user_by_email_not_exists(self, db_session: Session) -> None:
        """
        Test that verifies it returns None when user doesn't exist.
        Arrange: Empty database
        Act: Get user by non-existent email
        Assert: Should return None
        """
        result = user_repository.get_user_by_email(
            "nonexistent@example.com", db_session
        )

        assert result is None


class TestGetUserByUsername:
    """Tests for getting user by username from repository."""

    @patch("app.utils.passwords.pwd_context")
    def test_get_user_by_username_exists(
        self, mock_pwd_context: MagicMock, db_session: Session
    ) -> None:
        """
        Test that verifies getting an existing user by username.
        Arrange: User created in database with mocked hash
        Act: Get user by username
        Assert: Should return the correct user
        """
        from app.utils import passwords

        mock_hash = (
            "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        )
        mock_pwd_context.hash.return_value = mock_hash

        user = User(
            username="testuser",
            email="test@example.com",
            password=passwords.get_password_hash("password123"),
            created_at=datetime.now(),
        )
        db_session.add(user)
        db_session.commit()

        result = user_repository.get_user_by_username("testuser", db_session)

        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    def test_get_user_by_username_not_exists(self, db_session: Session) -> None:
        """
        Test que verifica que retorna None cuando el usuario no existe.
        Arrange: Base de datos vacía
        Act: Obtener usuario por username inexistente
        Assert: Debe retornar None
        """
        result = user_repository.get_user_by_username("nonexistent", db_session)

        assert result is None


class TestCreateUser:
    """Tests for creating user from repository."""

    def test_create_user_success(self, db_session: Session) -> None:
        """
        Test that verifies successful user creation.
        Arrange: Valid user data
        Act: Create user
        Assert: Should create user with correct data
        """
        hashed_password = "hashed_password_123"

        user = user_repository.create_user(
            email="newuser@example.com",
            username="newuser",
            hashed_password=hashed_password,
            db=db_session,
        )

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.password == hashed_password
        assert user.id is not None

    @patch("app.utils.passwords.pwd_context")
    def test_create_user_email_uniqueness(
        self, mock_pwd_context: MagicMock, db_session: Session
    ) -> None:
        """
        Test that verifies email must be unique.
        Arrange: Existing user with email and mocked hash
        Act: Try to create another user with same email
        Assert: Should raise IntegrityError
        """
        from app.utils import passwords
        from sqlalchemy.exc import IntegrityError

        mock_hash = (
            "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        )
        mock_pwd_context.hash.return_value = mock_hash

        # Crear primer usuario
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            password=passwords.get_password_hash("password123"),
            created_at=datetime.now(),
        )
        db_session.add(user1)
        db_session.commit()

        # Intentar crear segundo usuario con mismo email
        # El error se lanza en db.flush() dentro de create_user, no en commit
        with pytest.raises(IntegrityError):
            user_repository.create_user(
                email="duplicate@example.com",
                username="user2",
                hashed_password=passwords.get_password_hash("password456"),
                db=db_session,
            )

    @patch("app.utils.passwords.pwd_context")
    def test_create_user_username_uniqueness(
        self, mock_pwd_context: MagicMock, db_session: Session
    ) -> None:
        """
        Test that verifies username must be unique.
        Arrange: Existing user with username and mocked hash
        Act: Try to create another user with same username
        Assert: Should raise IntegrityError
        """
        from app.utils import passwords
        from sqlalchemy.exc import IntegrityError

        mock_hash = (
            "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        )
        mock_pwd_context.hash.return_value = mock_hash

        # Crear primer usuario
        user1 = User(
            username="duplicateuser",
            email="user1@example.com",
            password=passwords.get_password_hash("password123"),
            created_at=datetime.now(),
        )
        db_session.add(user1)
        db_session.commit()

        # Intentar crear segundo usuario con mismo username
        # El error se lanza en db.flush() dentro de create_user, no en commit
        with pytest.raises(IntegrityError):
            user_repository.create_user(
                email="user2@example.com",
                username="duplicateuser",
                hashed_password=passwords.get_password_hash("password456"),
                db=db_session,
            )


class TestCountUsers:
    """Tests for counting users from repository."""

    def test_count_users_empty(self, db_session: Session) -> None:
        """
        Test that verifies count when there are no users.
        Arrange: Empty database
        Act: Count users
        Assert: Should return 0
        """
        count = user_repository.count_users(db_session)

        assert count == 0

    @patch("app.utils.passwords.pwd_context")
    def test_count_users_multiple(
        self, mock_pwd_context: MagicMock, db_session: Session
    ) -> None:
        """
        Test that verifies correct count with multiple users.
        Arrange: Multiple users created with mocked hash
        Act: Count users
        Assert: Should return the correct number
        """
        from app.utils import passwords

        mock_hash = (
            "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        )
        mock_pwd_context.hash.return_value = mock_hash

        users = [
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password=passwords.get_password_hash("password123"),
                created_at=datetime.now(),
            )
            for i in range(5)
        ]

        for user in users:
            db_session.add(user)
        db_session.commit()

        count = user_repository.count_users(db_session)

        assert count == 5
