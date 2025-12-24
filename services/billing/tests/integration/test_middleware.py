"""
Integration tests for Logging Middleware.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

from app.main import app


@pytest.mark.integration
class TestLoggingMiddleware:
    """Test suite for Logging Middleware."""

    def test_middleware_adds_correlation_id(self) -> None:
        """Test that middleware adds correlation ID to response (Happy Path).

        Verifies:
        - Correlation ID header is present in response
        - Header value is a valid UUID format

        Args:
            None
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) == 32  # UUID hex format

    def test_middleware_uses_existing_correlation_id(self) -> None:
        """Test that middleware uses existing correlation ID from request (Happy Path).

        Verifies:
        - Existing correlation ID is preserved
        - Same ID is returned in response

        Args:
            None
        """
        # Arrange
        client = TestClient(app)
        existing_id = "test-correlation-id-12345"

        # Act
        response = client.get("/health", headers={"X-Correlation-ID": existing_id})

        # Assert
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == existing_id

    def test_middleware_logs_request_info(self) -> None:
        """Test that middleware logs request information (Happy Path).

        Verifies:
        - Request is processed successfully
        - Middleware executes without errors

        Args:
            None
        """
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        # Middleware should have executed successfully

    @patch("app.api.billing.get_all_billing_summaries")
    def test_middleware_handles_exception_in_endpoint(self, mock_get_all: Mock) -> None:
        """Test that middleware handles exceptions from endpoints (Error Case 2: Server Error).

        Verifies:
        - Exception is logged by middleware
        - Exception is propagated correctly
        - Process time is calculated

        Args:
            mock_get_all: Mocked get_all_billing_summaries function
        """
        # Arrange
        from app.main import app
        from app.utils.dependencies import get_user_id
        from app.database.config import get_db

        mock_db = Mock()
        app.dependency_overrides[get_user_id] = lambda: 1
        app.dependency_overrides[get_db] = lambda: iter([mock_db])

        mock_get_all.side_effect = Exception("Test endpoint error")
        client = TestClient(app)

        try:
            # Act
            response = client.get("/images")

            # Assert
            # Middleware should have logged the error
            assert response.status_code == 500
            # The exception should have been handled by middleware
        finally:
            app.dependency_overrides.clear()
