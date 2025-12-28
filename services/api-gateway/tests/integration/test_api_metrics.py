"""
Integration tests for Metrics API endpoints.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.services.metrics_collector import MetricsCollector
from app.services.user_id_cache import UserIdCache
from app.services.container_user_cache import ContainerUserCache


@pytest.mark.integration
class TestMetricsEndpoints:
    """Test suite for Metrics API endpoints."""

    def setup_method(self) -> None:
        """Setup method called before each test method."""
        # Initialize only metrics_collector and caches since TestClient doesn't trigger lifespan
        # We don't initialize full app state to avoid async task creation issues
        if not hasattr(app.state, "metrics_collector"):
            app.state.metrics_collector = MetricsCollector()
        if not hasattr(app.state, "user_id_cache"):
            app.state.user_id_cache = UserIdCache()
        if not hasattr(app.state, "container_user_cache"):
            app.state.container_user_cache = ContainerUserCache()
        # Initialize auth_client for tests that need it (even if mocked)
        if not hasattr(app.state, "auth_client"):
            from unittest.mock import Mock
            from app.clients.auth_client import AuthClient
            app.state.auth_client = Mock(spec=AuthClient)

    def test_get_metrics_returns_user_metrics(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics returns metrics for authenticated user.

        Verifies:
        - Endpoint returns 200 OK
        - Response contains user-specific metrics structure
        - Metrics include total_requests, total_errors, avg_latency_ms
        - Metrics are filtered by authenticated user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - Some recorded requests for user 1 and user 2

        Act:
        - Send GET request to /api/metrics

        Assert:
        - Status code is 200
        - Response contains only metrics for authenticated user (user_id=1)
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector

        # Record some test metrics for user 1 (authenticated user)
        metrics_collector.record_request(
            status_code=200,
            latency_ms=50.0,
            user_id=1,
            app_hostname="testapp.localhost",
            container_id="test-container",
        )
        metrics_collector.record_request(
            status_code=500,
            latency_ms=100.0,
            user_id=1,
            app_hostname="testapp.localhost",
            container_id="test-container",
        )
        # Record metrics for user 2 (should not appear in response)
        metrics_collector.record_request(
            status_code=200,
            latency_ms=30.0,
            user_id=2,
            app_hostname="other-app.localhost",
            container_id="other-container",
        )

        # Act
        response = authenticated_client.get("/api/metrics")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["user_id"] == 1  # Authenticated user
        assert "total_requests" in data
        assert "total_errors" in data
        assert "avg_latency_ms" in data
        assert "status_codes" in data
        assert data["total_requests"] == 2  # Only user 1's requests
        assert "by_app_hostname" in data
        assert "by_container" in data
        # Verify user 2's metrics are not included
        assert "other-app.localhost" not in data.get("by_app_hostname", {})
        assert "other-container" not in data.get("by_container", {})

        # Cleanup
        metrics_collector.reset()

    def test_get_metrics_filters_by_user_id(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics filters by authenticated user_id.

        Verifies:
        - Endpoint extracts user_id from authentication token
        - Returns only metrics for authenticated user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - Requests from multiple users

        Act:
        - Send GET request to /api/metrics (user_id extracted from token)

        Assert:
        - Status code is 200
        - Response contains only metrics for authenticated user (user_id=1)
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector

        # Record metrics for user 1 (authenticated user)
        metrics_collector.record_request(
            status_code=200, latency_ms=50.0, user_id=1, app_hostname="app1.localhost"
        )
        # Record metrics for user 2 (should not appear)
        metrics_collector.record_request(
            status_code=200, latency_ms=30.0, user_id=2, app_hostname="app2.localhost"
        )

        # Act
        response = authenticated_client.get("/api/metrics")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["user_id"] == 1  # Authenticated user
        assert data["total_requests"] == 1  # Only user 1's request
        assert "total_errors" in data
        assert "avg_latency_ms" in data

        # Cleanup
        metrics_collector.reset()

    def test_get_metrics_filters_by_app_hostname(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics filters by app_hostname for authenticated user.

        Verifies:
        - Endpoint accepts app_hostname query parameter
        - Returns only metrics for specified app_hostname that belongs to authenticated user
        - Validates that app_hostname belongs to authenticated user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - user_id_cache populated with app_hostname -> user_id mapping
        - Requests from multiple apps

        Act:
        - Send GET request to /api/metrics?app_hostname=testapp.localhost

        Assert:
        - Status code is 200
        - Response contains only metrics for testapp.localhost
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        user_id_cache: UserIdCache = app.state.user_id_cache

        # Set up cache: testapp.localhost belongs to user 1 (authenticated user)
        user_id_cache.set("testapp.localhost", 1)
        user_id_cache.set("otherapp.localhost", 2)  # Different user

        # Record metrics for different apps
        metrics_collector.record_request(
            status_code=200, latency_ms=50.0, user_id=1, app_hostname="testapp.localhost"
        )
        metrics_collector.record_request(
            status_code=200, latency_ms=30.0, user_id=2, app_hostname="otherapp.localhost"
        )

        # Act
        response = authenticated_client.get("/api/metrics?app_hostname=testapp.localhost")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["app_hostname"] == "testapp.localhost"
        assert data["total_requests"] == 1
        assert "total_errors" in data
        assert "avg_latency_ms" in data

        # Cleanup
        metrics_collector.reset()
        user_id_cache.remove("testapp.localhost")
        user_id_cache.remove("otherapp.localhost")

    def test_get_metrics_filters_by_container_id(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics filters by container_id for authenticated user.

        Verifies:
        - Endpoint accepts container_id query parameter
        - Returns only metrics for specified container that belongs to authenticated user
        - Validates that container_id belongs to authenticated user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - container_user_cache populated with container_id -> user_id mapping
        - Requests from multiple containers

        Act:
        - Send GET request to /api/metrics?container_id=test-container

        Assert:
        - Status code is 200
        - Response contains only metrics for test-container
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        container_user_cache: ContainerUserCache = app.state.container_user_cache

        # Set up cache: test-container belongs to user 1 (authenticated user)
        container_user_cache.set("test-container", 1)
        container_user_cache.set("other-container", 2)  # Different user

        # Record metrics for different containers
        metrics_collector.record_request(
            status_code=200, latency_ms=50.0, user_id=1, container_id="test-container"
        )
        metrics_collector.record_request(
            status_code=200, latency_ms=30.0, user_id=2, container_id="other-container"
        )

        # Act
        response = authenticated_client.get("/api/metrics?container_id=test-container")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["container_id"] == "test-container"
        assert data["total_requests"] == 1
        assert "total_errors" in data
        assert "avg_latency_ms" in data

        # Cleanup
        metrics_collector.reset()
        container_user_cache.remove("test-container")
        container_user_cache.remove("other-container")

    def test_get_metrics_returns_error_for_nonexistent_user(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics returns error when authenticated user has no metrics.

        Verifies:
        - Endpoint returns error message when authenticated user has no metrics

        Arrange:
        - FastAPI app with empty MetricsCollector
        - Authenticated client (user_id=1 from sample_user_response)

        Act:
        - Send GET request to /api/metrics

        Assert:
        - Status code is 200 (endpoint doesn't fail, just returns error message)
        - Response contains error message
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        metrics_collector.reset()  # Ensure empty

        # Act
        response = authenticated_client.get("/api/metrics")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "error" in data
        assert "No metrics found" in data["error"]

    def test_get_metrics_returns_error_for_nonexistent_app_hostname(
        self, authenticated_client: TestClient
    ) -> None:
        """Test that GET /api/metrics returns error for nonexistent app_hostname.

        Verifies:
        - Endpoint returns error message when app_hostname has no metrics
        - Validates that app_hostname belongs to authenticated user

        Arrange:
        - FastAPI app with empty MetricsCollector
        - Authenticated client (user_id=1 from sample_user_response)
        - user_id_cache with app_hostname -> user_id mapping

        Act:
        - Send GET request to /api/metrics?app_hostname=nonexistent.localhost

        Assert:
        - Status code is 200
        - Response contains error message
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        user_id_cache: UserIdCache = app.state.user_id_cache
        metrics_collector.reset()  # Ensure empty
        # Set cache so validation passes
        user_id_cache.set("nonexistent.localhost", 1)

        # Act
        response = authenticated_client.get("/api/metrics?app_hostname=nonexistent.localhost")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "error" in data
        assert "No metrics found" in data["error"]

        # Cleanup
        user_id_cache.remove("nonexistent.localhost")

    def test_get_metrics_returns_error_for_nonexistent_container(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics returns error for nonexistent container.

        Verifies:
        - Endpoint returns error message when container has no metrics
        - Validates that container_id belongs to authenticated user

        Arrange:
        - FastAPI app with empty MetricsCollector
        - Authenticated client (user_id=1 from sample_user_response)
        - container_user_cache with container_id -> user_id mapping

        Act:
        - Send GET request to /api/metrics?container_id=nonexistent

        Assert:
        - Status code is 200
        - Response contains error message
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        container_user_cache: ContainerUserCache = app.state.container_user_cache
        metrics_collector.reset()  # Ensure empty
        # Set cache so validation passes
        container_user_cache.set("nonexistent", 1)

        # Act
        response = authenticated_client.get("/api/metrics?container_id=nonexistent")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "error" in data
        assert "No metrics found" in data["error"]

        # Cleanup
        container_user_cache.remove("nonexistent")

    def test_get_metrics_with_empty_metrics(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics handles empty metrics gracefully for authenticated user.

        Verifies:
        - Endpoint returns error message when authenticated user has no metrics

        Arrange:
        - FastAPI app with empty MetricsCollector
        - Authenticated client (user_id=1 from sample_user_response)

        Act:
        - Send GET request to /api/metrics

        Assert:
        - Status code is 200
        - Response contains error message (not zero metrics, but error)
        """
        # Arrange
        metrics_collector: MetricsCollector = app.state.metrics_collector
        metrics_collector.reset()  # Ensure empty

        # Act
        response = authenticated_client.get("/api/metrics")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        # When user has no metrics, we return an error message
        assert "error" in data
        assert "No metrics found" in data["error"]

    def test_get_metrics_requires_authentication(self, client: TestClient) -> None:
        """Test that GET /api/metrics requires authentication.

        Verifies:
        - Endpoint returns 401 when no authentication token is provided

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Unauthenticated client

        Act:
        - Send GET request to /api/metrics without authentication

        Assert:
        - Status code is 401
        - Response indicates authentication required
        """
        # Arrange - client is unauthenticated

        # Act
        response = client.get("/api/metrics")

        # Assert
        assert (
            response.status_code == 401
        ), f"Expected 401, got {response.status_code}: {response.text}"

        data = response.json()
        assert "detail" in data
        assert "authentication" in data["detail"].lower() or "required" in data["detail"].lower()

    def test_get_metrics_rejects_other_user_app_hostname(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics rejects app_hostname that doesn't belong to authenticated user.

        Verifies:
        - Endpoint returns 403 when app_hostname belongs to another user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - user_id_cache with app_hostname -> user_id mapping (app belongs to user 2)

        Act:
        - Send GET request to /api/metrics?app_hostname=other-user-app.localhost

        Assert:
        - Status code is 403
        - Response indicates forbidden access
        """
        # Arrange
        user_id_cache: UserIdCache = app.state.user_id_cache
        # Set cache: app belongs to user 2, not authenticated user (user 1)
        user_id_cache.set("other-user-app.localhost", 2)

        # Act
        response = authenticated_client.get("/api/metrics?app_hostname=other-user-app.localhost")

        # Assert
        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}: {response.text}"

        data = response.json()
        assert "detail" in data
        assert "don't have access" in data["detail"].lower() or "forbidden" in data["detail"].lower()

        # Cleanup
        user_id_cache.remove("other-user-app.localhost")

    def test_get_metrics_rejects_other_user_container(self, authenticated_client: TestClient) -> None:
        """Test that GET /api/metrics rejects container_id that doesn't belong to authenticated user.

        Verifies:
        - Endpoint returns 403 when container_id belongs to another user

        Arrange:
        - FastAPI app with MetricsCollector initialized
        - Authenticated client (user_id=1 from sample_user_response)
        - container_user_cache with container_id -> user_id mapping (container belongs to user 2)

        Act:
        - Send GET request to /api/metrics?container_id=other-user-container

        Assert:
        - Status code is 403
        - Response indicates forbidden access
        """
        # Arrange
        container_user_cache: ContainerUserCache = app.state.container_user_cache
        # Set cache: container belongs to user 2, not authenticated user (user 1)
        container_user_cache.set("other-user-container", 2)

        # Act
        response = authenticated_client.get("/api/metrics?container_id=other-user-container")

        # Assert
        assert (
            response.status_code == 403
        ), f"Expected 403, got {response.status_code}: {response.text}"

        data = response.json()
        assert "detail" in data
        assert "don't have access" in data["detail"].lower() or "forbidden" in data["detail"].lower()

        # Cleanup
        container_user_cache.remove("other-user-container")

