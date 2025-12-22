"""
Shared fixtures and configuration for all tests.

This module provides:
- Database session mocks
- Test data fixtures
- Application setup fixtures
- Common test utilities
"""
import sys
import os
from typing import Generator, Dict, Any, List
from unittest.mock import MagicMock, Mock
import pytest
from fastapi.testclient import TestClient

# Set DATABASE_URL before any imports that might need it
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')


def pytest_configure(config):
    """Hook that runs before test modules are imported.
    
    Args:
        config: Pytest configuration object
    """
    # Mock external dependencies before module imports
    sys.modules["psycopg2"] = MagicMock()
    sys.modules["confluent_kafka"] = MagicMock()


@pytest.fixture
def db_session_mock() -> Mock:
    """Fixture providing a mock SQLAlchemy database session.
    
    Returns:
        Mock: A mock database session with common methods (commit, rollback, etc.)
    """
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.refresh = Mock()
    db.flush = Mock()
    db.delete = Mock()
    db.execute = Mock(return_value=Mock())
    db.query = Mock()
    return db


@pytest.fixture
def test_user_id() -> int:
    """Fixture providing a test user ID.
    
    Returns:
        int: Test user ID (1)
    """
    return 1


@pytest.fixture
def sample_image_data() -> Dict[str, Any]:
    """Fixture providing sample image creation data.
    
    Returns:
        Dict[str, Any]: Dictionary with image creation parameters
    """
    return {
        "name": "test-app",
        "tag": "latest",
        "app_hostname": "test.example.com",
        "container_port": 8080,
        "min_instances": 1,
        "max_instances": 3,
        "cpu_limit": "0.5",
        "memory_limit": "512m",
    }


@pytest.fixture
def sample_image_file() -> tuple:
    """Fixture providing a sample image file for upload.
    
    Returns:
        tuple: (filename, content, content_type) for multipart upload
    """
    return ("test.zip", b"fake zip content", "application/zip")


@pytest.fixture
def sample_container_data() -> Dict[str, Any]:
    """Fixture providing sample container creation data.
    
    Returns:
        Dict[str, Any]: Dictionary with container creation parameters
    """
    return {
        "name": "test-container",
        "image_id": 1,
        "count": 1,
    }


@pytest.fixture
def invalid_image_data() -> Dict[str, Any]:
    """Fixture providing invalid image creation data for error testing.
    
    Returns:
        Dict[str, Any]: Dictionary with invalid parameters (negative port, invalid limits)
    """
    return {
        "name": "",  # Empty name
        "tag": "",  # Empty tag
        "app_hostname": "invalid..hostname",  # Invalid hostname
        "container_port": -1,  # Invalid port
        "min_instances": 10,
        "max_instances": 1,  # min > max
        "cpu_limit": "",
        "memory_limit": "",
    }