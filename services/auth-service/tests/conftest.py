"""
Shared fixtures for auth-service tests.
"""

import os
from typing import Generator
from datetime import datetime
from unittest.mock import Mock, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure DATABASE_URL before importing app.main to avoid validation
# We use a valid PostgreSQL URL to pass validation, but in tests we use SQLite
# Validation requires: postgresql:// or postgresql+psycopg2://, hostname, and database name
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql://testuser:testpass@localhost:5432/testdb"

from app.main import app
from app.database.models import Base, User
from app.database.config import get_db


# In-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Fixture that provides a database session for tests.
    Creates tables before each test and drops them after.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db() -> Mock:
    """
    Fixture that provides a mock database session.
    """
    return Mock(spec=Session)


@pytest.fixture
def override_get_db(db_session: Session):
    """
    Fixture that overrides the get_db dependency to use the test database.
    """

    def _get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    yield db_session
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(override_get_db) -> TestClient:
    """
    Fixture that provides a FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def sample_user_data() -> dict:
    """
    Fixture that provides test user data.
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_user_create():
    """
    Fixture that provides a test UserCreate object.
    """
    from app.schemas.user import UserCreate

    return UserCreate(
        username="testuser", email="test@example.com", password="testpassword123"
    )


@pytest.fixture
def sample_login_request():
    """
    Fixture that provides a test LoginRequest object.
    """
    from app.schemas.user import LoginRequest

    return LoginRequest(email="test@example.com", password="testpassword123")


@pytest.fixture(autouse=True)
def mock_passlib(monkeypatch):
    """
    Fixture that mocks passlib for all tests to avoid initialization issues.
    Runs automatically for all tests.
    """
    from app.utils import passwords

    # Create mock of passlib context
    mock_pwd_context = MagicMock()

    # Simulated valid bcrypt hash for tests
    # This hash will be used for all passwords in tests
    test_hash = (
        "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
    )

    # Configure mock for hash
    def mock_hash(password: str) -> str:
        # Return the same hash for all passwords in tests
        # In real tests, this can be adjusted
        return test_hash

    # Configure mock for verify
    def mock_verify(plain: str, hashed: str) -> bool:
        # If the hash is test_hash and password is one of the known ones, return True
        if hashed == test_hash:
            # Accept common test passwords
            if plain in ["testpassword123", "password123", "securepass123", "pass123"]:
                return True
        return False

    mock_pwd_context.hash.side_effect = mock_hash
    mock_pwd_context.verify.side_effect = mock_verify

    # Replace pwd_context in passwords module
    monkeypatch.setattr(passwords, "pwd_context", mock_pwd_context)


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """
    Fixture that creates and returns a test user in the database.
    """
    from app.utils import passwords

    user = User(
        username="testuser",
        email="test@example.com",
        password=passwords.get_password_hash("testpassword123"),
        created_at=datetime.now(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_mock() -> Mock:
    """
    Fixture that provides a mock user.
    """
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password = "hashed_password"
    user.created_at = datetime.now()
    return user


@pytest.fixture
def invalid_user_data() -> dict:
    """
    Fixture that provides invalid user data for error tests.
    """
    return {
        "username": "",
        "email": "invalid-email",
        "password": "123",  # Password muy corto
    }


@pytest.fixture
def non_existent_user_data() -> dict:
    """
    Fixture that provides user data that doesn't exist in the database.
    """
    return {"email": "nonexistent@example.com", "password": "somepassword123"}


@pytest.fixture
def mock_token() -> str:
    """
    Fixture that provides a mock JWT token for tests.
    """
    return "mock.jwt.token.here"


@pytest.fixture
def expired_token() -> str:
    """
    Fixture that provides an expired JWT token for tests.
    """
    import jwt
    from datetime import datetime, timedelta, timezone
    from app.utils.config import SECRET_KEY, ALGORITHM

    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def invalid_token() -> str:
    """
    Fixture that provides an invalid JWT token for tests.
    """
    return "invalid.token.here"
