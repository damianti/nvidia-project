"""
Unit tests for Metrics Collector.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""

import pytest

from app.services.metrics_collector import MetricsCollector


@pytest.mark.unit
class TestMetricsCollector:
    """Test suite for MetricsCollector class."""

    def test_init_creates_empty_metrics(self) -> None:
        """Test that MetricsCollector initializes with empty metrics.

        Verifies:
        - All counters start at 0
        - All metric dictionaries are empty

        Arrange:
        - None (fresh instance)

        Act:
        - Create MetricsCollector instance

        Assert:
        - All metrics are zero/empty
        """
        # Arrange & Act
        collector = MetricsCollector()

        # Assert
        assert collector.total_requests == 0
        assert collector.total_errors == 0
        assert collector.latency_sum == 0.0
        assert collector.latency_count == 0
        assert len(collector.status_codes) == 0
        assert len(collector.user_metrics) == 0
        assert len(collector.app_hostname_metrics) == 0
        assert len(collector.container_metrics) == 0

    def test_record_request_updates_global_metrics(self) -> None:
        """Test that record_request updates global metrics.

        Verifies:
        - Total requests increments
        - Status codes are tracked
        - Errors are counted correctly
        - Latency is accumulated

        Arrange:
        - MetricsCollector instance

        Act:
        - Record multiple requests with different status codes and latencies

        Assert:
        - Global metrics reflect all recorded requests
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(status_code=200, latency_ms=50.0)
        collector.record_request(status_code=404, latency_ms=30.0)
        collector.record_request(status_code=500, latency_ms=100.0)

        # Assert
        assert collector.total_requests == 3
        assert collector.total_errors == 2  # 404 and 500
        assert collector.status_codes["200"] == 1
        assert collector.status_codes["404"] == 1
        assert collector.status_codes["500"] == 1
        assert collector.latency_sum == 180.0
        assert collector.latency_count == 3

    def test_record_request_tracks_by_user_id(self) -> None:
        """Test that record_request tracks metrics by user_id.

        Verifies:
        - User-specific metrics are tracked separately
        - Multiple users can have independent metrics

        Arrange:
        - MetricsCollector instance

        Act:
        - Record requests for different users

        Assert:
        - Each user has correct metrics
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(
            status_code=200, latency_ms=50.0, user_id=1
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, user_id=1
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, user_id=2
        )

        # Assert
        assert collector.user_metrics[1]["requests"] == 2
        assert collector.user_metrics[1]["errors"] == 1
        assert collector.user_metrics[1]["latency_sum"] == 150.0
        assert collector.user_metrics[1]["latency_count"] == 2
        assert collector.user_metrics[2]["requests"] == 1
        assert collector.user_metrics[2]["errors"] == 0

    def test_record_request_tracks_by_app_hostname(self) -> None:
        """Test that record_request tracks metrics by app_hostname.

        Verifies:
        - App hostname-specific metrics are tracked separately
        - Multiple apps can have independent metrics

        Arrange:
        - MetricsCollector instance

        Act:
        - Record requests for different app hostnames

        Assert:
        - Each app hostname has correct metrics
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(
            status_code=200, latency_ms=50.0, app_hostname="app1.localhost"
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, app_hostname="app1.localhost"
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, app_hostname="app2.localhost"
        )

        # Assert
        assert collector.app_hostname_metrics["app1.localhost"]["requests"] == 2
        assert collector.app_hostname_metrics["app1.localhost"]["errors"] == 1
        assert (
            collector.app_hostname_metrics["app1.localhost"]["latency_sum"] == 150.0
        )
        assert (
            collector.app_hostname_metrics["app1.localhost"]["latency_count"] == 2
        )
        assert collector.app_hostname_metrics["app2.localhost"]["requests"] == 1
        assert collector.app_hostname_metrics["app2.localhost"]["errors"] == 0

    def test_record_request_tracks_by_container_id(self) -> None:
        """Test that record_request tracks metrics by container_id.

        Verifies:
        - Container-specific metrics are tracked separately
        - Multiple containers can have independent metrics

        Arrange:
        - MetricsCollector instance

        Act:
        - Record requests for different containers

        Assert:
        - Each container has correct metrics
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(
            status_code=200, latency_ms=50.0, container_id="container1"
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, container_id="container1"
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, container_id="container2"
        )

        # Assert
        assert collector.container_metrics["container1"]["requests"] == 2
        assert collector.container_metrics["container1"]["errors"] == 1
        assert collector.container_metrics["container1"]["latency_sum"] == 150.0
        assert collector.container_metrics["container1"]["latency_count"] == 2
        assert collector.container_metrics["container2"]["requests"] == 1
        assert collector.container_metrics["container2"]["errors"] == 0

    def test_record_request_with_all_dimensions(self) -> None:
        """Test that record_request tracks metrics across all dimensions simultaneously.

        Verifies:
        - A single request can be tracked by user, app_hostname, and container
        - All dimensions are updated correctly

        Arrange:
        - MetricsCollector instance

        Act:
        - Record a request with all dimensions

        Assert:
        - All dimensions reflect the request
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(
            status_code=200,
            latency_ms=50.0,
            user_id=1,
            app_hostname="app1.localhost",
            container_id="container1",
        )

        # Assert
        assert collector.user_metrics[1]["requests"] == 1
        assert collector.app_hostname_metrics["app1.localhost"]["requests"] == 1
        assert collector.container_metrics["container1"]["requests"] == 1
        assert collector.total_requests == 1

    def test_record_request_with_zero_latency(self) -> None:
        """Test that record_request handles zero latency correctly.

        Verifies:
        - Zero latency doesn't affect latency_sum or latency_count
        - Request is still counted

        Arrange:
        - MetricsCollector instance

        Act:
        - Record request with zero latency

        Assert:
        - Request is counted but latency is not accumulated
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        collector.record_request(status_code=200, latency_ms=0.0)

        # Assert
        assert collector.total_requests == 1
        assert collector.latency_sum == 0.0
        assert collector.latency_count == 0

    def test_get_metrics_returns_global_metrics_when_no_filters(self) -> None:
        """Test that get_metrics returns global metrics when no filters provided.

        Verifies:
        - Returns aggregated metrics
        - Includes breakdown by user, app_hostname, and container
        - Calculates average latency correctly

        Arrange:
        - MetricsCollector with recorded requests

        Act:
        - Call get_metrics without filters

        Assert:
        - Returns correct global metrics structure
        """
        # Arrange
        collector = MetricsCollector()
        collector.record_request(
            status_code=200,
            latency_ms=50.0,
            user_id=1,
            app_hostname="app1.localhost",
            container_id="container1",
        )
        collector.record_request(
            status_code=500,
            latency_ms=100.0,
            user_id=1,
            app_hostname="app1.localhost",
            container_id="container1",
        )

        # Act
        metrics = collector.get_metrics()

        # Assert
        assert metrics["total_requests"] == 2
        assert metrics["total_errors"] == 1
        assert metrics["avg_latency_ms"] == 75.0
        assert "by_user" in metrics
        assert "by_app_hostname" in metrics
        assert "by_container" in metrics
        assert "1" in metrics["by_user"]
        assert "app1.localhost" in metrics["by_app_hostname"]
        assert "container1" in metrics["by_container"]

    def test_get_metrics_filters_by_user_id(self) -> None:
        """Test that get_metrics filters by user_id.

        Verifies:
        - Returns only metrics for specified user
        - Calculates average latency correctly
        - Includes by_app_hostname and by_container filtered by user_id

        Arrange:
        - MetricsCollector with requests from multiple users, app_hostnames, and containers

        Act:
        - Call get_metrics with user_id filter

        Assert:
        - Returns only metrics for that user
        - by_app_hostname and by_container are filtered by user_id
        """
        # Arrange
        collector = MetricsCollector()
        # User 1 metrics
        collector.record_request(
            status_code=200, latency_ms=50.0, user_id=1, app_hostname="app1.localhost", container_id="container1"
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, user_id=1, app_hostname="app1.localhost", container_id="container1"
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, user_id=1, app_hostname="app2.localhost", container_id="container2"
        )
        # User 2 metrics
        collector.record_request(
            status_code=200, latency_ms=20.0, user_id=2, app_hostname="app3.localhost", container_id="container3"
        )

        # Act
        metrics = collector.get_metrics(user_id=1)

        # Assert
        assert metrics["user_id"] == 1
        assert metrics["total_requests"] == 3
        assert metrics["total_errors"] == 1
        assert metrics["avg_latency_ms"] == 60.0  # (50 + 100 + 30) / 3
        assert metrics["status_codes"]["200"] == 2
        assert metrics["status_codes"]["500"] == 1
        
        # Verify by_app_hostname is filtered by user_id
        assert "by_app_hostname" in metrics
        assert "app1.localhost" in metrics["by_app_hostname"]
        assert "app2.localhost" in metrics["by_app_hostname"]
        assert "app3.localhost" not in metrics["by_app_hostname"]  # User 2's app
        
        # Verify by_container is filtered by user_id
        assert "by_container" in metrics
        assert "container1" in metrics["by_container"]
        assert "container2" in metrics["by_container"]
        assert "container3" not in metrics["by_container"]  # User 2's container

    def test_get_metrics_filters_by_app_hostname(self) -> None:
        """Test that get_metrics filters by app_hostname.

        Verifies:
        - Returns only metrics for specified app_hostname
        - Calculates average latency correctly

        Arrange:
        - MetricsCollector with requests from multiple apps

        Act:
        - Call get_metrics with app_hostname filter

        Assert:
        - Returns only metrics for that app_hostname
        """
        # Arrange
        collector = MetricsCollector()
        collector.record_request(
            status_code=200, latency_ms=50.0, app_hostname="app1.localhost"
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, app_hostname="app1.localhost"
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, app_hostname="app2.localhost"
        )

        # Act
        metrics = collector.get_metrics(app_hostname="app1.localhost")

        # Assert
        assert metrics["app_hostname"] == "app1.localhost"
        assert metrics["total_requests"] == 2
        assert metrics["total_errors"] == 1
        assert metrics["avg_latency_ms"] == 75.0
        assert metrics["status_codes"]["200"] == 1
        assert metrics["status_codes"]["500"] == 1

    def test_get_metrics_filters_by_container_id(self) -> None:
        """Test that get_metrics filters by container_id.

        Verifies:
        - Returns only metrics for specified container
        - Calculates average latency correctly

        Arrange:
        - MetricsCollector with requests from multiple containers

        Act:
        - Call get_metrics with container_id filter

        Assert:
        - Returns only metrics for that container
        """
        # Arrange
        collector = MetricsCollector()
        collector.record_request(
            status_code=200, latency_ms=50.0, container_id="container1"
        )
        collector.record_request(
            status_code=500, latency_ms=100.0, container_id="container1"
        )
        collector.record_request(
            status_code=200, latency_ms=30.0, container_id="container2"
        )

        # Act
        metrics = collector.get_metrics(container_id="container1")

        # Assert
        assert metrics["container_id"] == "container1"
        assert metrics["total_requests"] == 2
        assert metrics["total_errors"] == 1
        assert metrics["avg_latency_ms"] == 75.0
        assert metrics["status_codes"]["200"] == 1
        assert metrics["status_codes"]["500"] == 1

    def test_get_metrics_returns_error_for_nonexistent_user(self) -> None:
        """Test that get_metrics returns error for nonexistent user.

        Verifies:
        - Returns error message when user has no metrics

        Arrange:
        - Empty MetricsCollector

        Act:
        - Call get_metrics with nonexistent user_id

        Assert:
        - Returns error message
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        metrics = collector.get_metrics(user_id=999)

        # Assert
        assert "error" in metrics
        assert "No metrics found" in metrics["error"]

    def test_get_metrics_returns_error_for_nonexistent_app_hostname(
        self,
    ) -> None:
        """Test that get_metrics returns error for nonexistent app_hostname.

        Verifies:
        - Returns error message when app_hostname has no metrics

        Arrange:
        - Empty MetricsCollector

        Act:
        - Call get_metrics with nonexistent app_hostname

        Assert:
        - Returns error message
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        metrics = collector.get_metrics(app_hostname="nonexistent.localhost")

        # Assert
        assert "error" in metrics
        assert "No metrics found" in metrics["error"]

    def test_get_metrics_returns_error_for_nonexistent_container(self) -> None:
        """Test that get_metrics returns error for nonexistent container.

        Verifies:
        - Returns error message when container has no metrics

        Arrange:
        - Empty MetricsCollector

        Act:
        - Call get_metrics with nonexistent container_id

        Assert:
        - Returns error message
        """
        # Arrange
        collector = MetricsCollector()

        # Act
        metrics = collector.get_metrics(container_id="nonexistent")

        # Assert
        assert "error" in metrics
        assert "No metrics found" in metrics["error"]

    def test_get_metrics_calculates_average_latency_correctly(self) -> None:
        """Test that get_metrics calculates average latency correctly.

        Verifies:
        - Average latency is calculated correctly
        - Handles zero latency_count gracefully

        Arrange:
        - MetricsCollector with requests

        Act:
        - Call get_metrics

        Assert:
        - Average latency is correct
        """
        # Arrange
        collector = MetricsCollector()
        collector.record_request(status_code=200, latency_ms=50.0)
        collector.record_request(status_code=200, latency_ms=100.0)
        collector.record_request(status_code=200, latency_ms=0.0)  # Should not count

        # Act
        metrics = collector.get_metrics()

        # Assert
        assert metrics["avg_latency_ms"] == 75.0  # (50 + 100) / 2

    def test_reset_clears_all_metrics(self) -> None:
        """Test that reset clears all metrics.

        Verifies:
        - All counters are reset to zero
        - All dictionaries are cleared

        Arrange:
        - MetricsCollector with recorded requests

        Act:
        - Call reset

        Assert:
        - All metrics are cleared
        """
        # Arrange
        collector = MetricsCollector()
        collector.record_request(
            status_code=200,
            latency_ms=50.0,
            user_id=1,
            app_hostname="app1.localhost",
            container_id="container1",
        )

        # Act
        collector.reset()

        # Assert
        assert collector.total_requests == 0
        assert collector.total_errors == 0
        assert collector.latency_sum == 0.0
        assert collector.latency_count == 0
        assert len(collector.status_codes) == 0
        assert len(collector.user_metrics) == 0
        assert len(collector.app_hostname_metrics) == 0
        assert len(collector.container_metrics) == 0

