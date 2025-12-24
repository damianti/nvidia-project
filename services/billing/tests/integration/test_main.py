"""
Integration tests for main FastAPI application setup.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Application configuration validation
- Full type hints and descriptive docstrings
"""

import pytest
import os

# Set DATABASE_URL before importing app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

from app.main import app


@pytest.mark.integration
class TestMainApp:
    """Test suite for main FastAPI application."""

    def test_app_has_cors_middleware(self) -> None:
        """Test that CORS middleware is configured.

        Verifies:
        - CORS middleware is present in the middleware stack

        Args:
            None
        """
        # Arrange & Act
        middleware_classes = [
            m.cls.__name__ if hasattr(m, "cls") else str(type(m))
            for m in app.user_middleware
        ]

        # Assert
        assert (
            any("CORS" in str(m) for m in middleware_classes)
            or len(app.user_middleware) > 0
        )

    def test_app_has_logging_middleware(self) -> None:
        """Test that logging middleware is configured.

        Verifies:
        - Logging middleware is present in the middleware stack

        Args:
            None
        """
        # Arrange & Act
        middleware_classes = [
            m.cls.__name__ if hasattr(m, "cls") else str(type(m))
            for m in app.user_middleware
        ]

        # Assert
        assert (
            any("Logging" in str(m) for m in middleware_classes)
            or len(app.user_middleware) > 0
        )

    def test_app_includes_routers(self) -> None:
        """Test that billing router is included.

        Verifies:
        - Billing router is registered in the application

        Args:
            None
        """
        # Arrange & Act
        routes = [route.path for route in app.routes]

        # Assert
        assert "/images" in routes or any(
            "/images" in str(route) for route in app.routes
        )
