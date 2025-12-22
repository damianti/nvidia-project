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
from datetime import datetime, timezone, timedelta
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
    db.add = Mock()
    db.query = Mock()
    db.execute = Mock(return_value=Mock())
    return db


@pytest.fixture
def test_user_id() -> int:
    """Fixture providing a test user ID.
    
    Returns:
        int: Test user ID (1)
    """
    return 1


@pytest.fixture
def test_image_id() -> int:
    """Fixture providing a test image ID.
    
    Returns:
        int: Test image ID (1)
    """
    return 1


@pytest.fixture
def sample_container_event_data() -> Dict[str, Any]:
    """Fixture providing sample container event data.
    
    Returns:
        Dict[str, Any]: Dictionary with container event parameters
    """
    return {
        "event": "container.created",
        "container_id": "docker-123",
        "container_name": "test-container",
        "container_ip": "172.17.0.2",
        "image_id": 1,
        "internal_port": 8080,
        "external_port": 32768,
        "app_hostname": "test.example.com",
        "user_id": 1,
        "timestamp": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_billing_record() -> Mock:
    """Fixture providing a sample billing record mock.
    
    Returns:
        Mock: A mock Billing record with common attributes
    """
    from app.database.models import BillingStatus
    
    record = Mock()
    record.id = 1
    record.user_id = 1
    record.image_id = 1
    record.container_id = "docker-123"
    record.start_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    record.end_time = datetime.now(timezone.utc)
    record.duration_minutes = 30
    record.cost = 0.30
    record.status = BillingStatus.COMPLETED
    return record


@pytest.fixture
def sample_active_billing_record() -> Mock:
    """Fixture providing a sample active billing record mock.
    
    Returns:
        Mock: A mock active Billing record
    """
    from app.database.models import BillingStatus
    
    record = Mock()
    record.id = 2
    record.user_id = 1
    record.image_id = 1
    record.container_id = "docker-456"
    record.start_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    record.end_time = None
    record.duration_minutes = None
    record.cost = None
    record.status = BillingStatus.ACTIVE
    return record


@pytest.fixture
def sample_billing_summary_response() -> Dict[str, Any]:
    """Fixture providing sample billing summary response data.
    
    Returns:
        Dict[str, Any]: Dictionary with billing summary response structure
    """
    return {
        "image_id": 1,
        "total_containers": 2,
        "total_minutes": 45,
        "total_cost": 0.45,
        "active_containers": 1,
        "last_activity": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_billing_detail_response() -> Dict[str, Any]:
    """Fixture providing sample billing detail response data.
    
    Returns:
        Dict[str, Any]: Dictionary with billing detail response structure
    """
    return {
        "image_id": 1,
        "summary": {
            "image_id": 1,
            "total_containers": 2,
            "total_minutes": 45,
            "total_cost": 0.45,
            "active_containers": 1,
            "last_activity": datetime.now(timezone.utc).isoformat()
        },
        "containers": [
            {
                "id": 1,
                "container_id": "docker-123",
                "start_time": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": 30,
                "cost": 0.30,
                "status": "Completed"
            }
        ]
    }
