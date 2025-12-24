"""
Shared pytest configuration and fixtures for API Gateway tests.

This module imports all fixtures from the fixtures directory
and provides application-level test setup.
"""

import pytest
import os
import sys
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, MagicMock
from fastapi.testclient import TestClient

# Set environment variables before importing app
os.environ.setdefault("AUTH_SERVICE_URL", "http://auth-service:3005")
os.environ.setdefault("LOAD_BALANCER_URL", "http://load-balancer:3004")
os.environ.setdefault("ORCHESTRATOR_URL", "http://orchestrator:3003")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("CACHE_CLEANUP_INTERVAL", "300")

# Mock external dependencies before importing app
sys.modules["psycopg2"] = MagicMock()
sys.modules["confluent_kafka"] = MagicMock()

from app.main import app  # noqa: E402

# Import all fixtures from fixture modules
# This makes them available to all tests
# Using pytest_plugins ensures fixtures are discovered by pytest
pytest_plugins = [
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.routing_fixtures",
    "tests.fixtures.client_fixtures",
]


@pytest.fixture
def authenticated_client(
    client: TestClient,
    mock_auth_client: Mock,
    sample_user_response: Dict[str, Any],
    sample_auth_token: str,
) -> TestClient:
    """Fixture providing a TestClient with authentication setup.

    Args:
        client: TestClient fixture.
        mock_auth_client: Mocked auth client.
        sample_user_response: Sample user response data.
        sample_auth_token: Sample auth token.

    Returns:
        TestClient with authentication cookies set.
    """
    # Override auth_client dependency
    from app.utils.dependencies import get_auth_client

    app.dependency_overrides[get_auth_client] = lambda: mock_auth_client

    # Mock successful authentication
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = sample_user_response
    mock_auth_client.get_current_user = AsyncMock(return_value=mock_response)

    # Set authentication cookie
    client.cookies.set("access_token", sample_auth_token)

    yield client

    # Cleanup
    app.dependency_overrides.clear()
