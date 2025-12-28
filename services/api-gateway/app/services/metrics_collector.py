# services/api-gateway/app/services/metrics_collector.py
"""
Metrics Collector for API Gateway.

Tracks request metrics by user, app_hostname, and container.
Stores user_id directly in app_hostname and container metrics for efficient filtering,
eliminating the need for external caches when querying metrics by user.
"""

import logging
from typing import Dict, Any, Optional
from collections import defaultdict

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class MetricsCollector:
    """Collects and aggregates metrics for the API Gateway."""

    def __init__(self):
        """Initialize metrics collector with empty counters."""
        # Global metrics
        self.total_requests = 0
        self.total_errors = 0
        self.status_codes: Dict[str, int] = defaultdict(int)
        self.latency_sum = 0.0
        self.latency_count = 0

        # Metrics by user_id
        self.user_metrics: Dict[int, Dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "errors": 0,
                "status_codes": defaultdict(int),
                "latency_sum": 0.0,
                "latency_count": 0,
            }
        )

        # Metrics by app_hostname (more natural for API Gateway as it's what arrives in requests)
        # Stores user_id directly in metrics for efficient filtering
        self.app_hostname_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "user_id": None,  # Store user_id directly for filtering
                "requests": 0,
                "errors": 0,
                "status_codes": defaultdict(int),
                "latency_sum": 0.0,
                "latency_count": 0,
            }
        )

        # Metrics by container_id
        # Stores user_id directly in metrics for efficient filtering
        self.container_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "user_id": None,  # Store user_id directly for filtering
                "requests": 0,
                "errors": 0,
                "status_codes": defaultdict(int),
                "latency_sum": 0.0,
                "latency_count": 0,
            }
        )

    def record_request(
        self,
        status_code: int,
        latency_ms: float = 0.0,
        user_id: Optional[int] = None,
        app_hostname: Optional[str] = None,
        container_id: Optional[str] = None,
    ) -> None:
        """
        Record a request with its metrics.

        Args:
            status_code: HTTP status code of the response
            latency_ms: Request latency in milliseconds
            user_id: User ID (optional)
            app_hostname: App hostname (optional, more natural for API Gateway)
            container_id: Container ID (optional)
        """
        # Global metrics
        self.total_requests += 1
        self.status_codes[str(status_code)] += 1

        if status_code >= 400:
            self.total_errors += 1

        if latency_ms > 0:
            self.latency_sum += latency_ms
            self.latency_count += 1

        # Metrics by user_id
        if user_id is not None:
            user_metrics = self.user_metrics[user_id]
            user_metrics["requests"] += 1
            user_metrics["status_codes"][str(status_code)] += 1
            if status_code >= 400:
                user_metrics["errors"] += 1
            if latency_ms > 0:
                user_metrics["latency_sum"] += latency_ms
                user_metrics["latency_count"] += 1

        # Metrics by app_hostname (more natural for API Gateway)
        if app_hostname is not None:
            app_metrics = self.app_hostname_metrics[app_hostname]
            # Store user_id if provided (for efficient filtering later)
            # Only set if None to avoid overwriting (first assignment is authoritative)
            if user_id is not None and app_metrics.get("user_id") is None:
                app_metrics["user_id"] = user_id
            app_metrics["requests"] += 1
            app_metrics["status_codes"][str(status_code)] += 1
            if status_code >= 400:
                app_metrics["errors"] += 1
            if latency_ms > 0:
                app_metrics["latency_sum"] += latency_ms
                app_metrics["latency_count"] += 1

        # Metrics by container_id
        if container_id is not None:
            container_metrics = self.container_metrics[container_id]
            # Store user_id if provided (for efficient filtering later)
            # Only set if None to avoid overwriting (first assignment is authoritative)
            if user_id is not None and container_metrics.get("user_id") is None:
                container_metrics["user_id"] = user_id
            container_metrics["requests"] += 1
            container_metrics["status_codes"][str(status_code)] += 1
            if status_code >= 400:
                container_metrics["errors"] += 1
            if latency_ms > 0:
                container_metrics["latency_sum"] += latency_ms
                container_metrics["latency_count"] += 1

    def get_metrics(
        self,
        user_id: Optional[int] = None,
        app_hostname: Optional[str] = None,
        container_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get metrics summary, optionally filtered by dimension.

        Args:
            user_id: Filter by user ID
            app_hostname: Filter by app hostname
            container_id: Filter by container ID

        Returns:
            Dictionary containing metrics
        """
        # If filters are provided, return filtered metrics
        if user_id is not None:
            user_metrics = self.user_metrics.get(user_id, {})
            if not user_metrics:
                return {"error": "No metrics found for this user"}
            avg_latency = (
                user_metrics["latency_sum"] / user_metrics["latency_count"]
                if user_metrics["latency_count"] > 0
                else 0.0
            )
            
            # Filter by_app_hostname and by_container for this user
            # Use user_id stored directly in metrics (no cache lookup needed)
            by_app_hostname = {
                hostname: {
                    "requests": metrics["requests"],
                    "errors": metrics["errors"],
                    "avg_latency_ms": round(
                        metrics["latency_sum"] / metrics["latency_count"]
                        if metrics["latency_count"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for hostname, metrics in self.app_hostname_metrics.items()
                if metrics.get("user_id") == user_id
            }
            
            by_container = {
                cid: {
                    "requests": metrics["requests"],
                    "errors": metrics["errors"],
                    "avg_latency_ms": round(
                        metrics["latency_sum"] / metrics["latency_count"]
                        if metrics["latency_count"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for cid, metrics in self.container_metrics.items()
                if metrics.get("user_id") == user_id
            }
            
            result = {
                "user_id": user_id,
                "total_requests": user_metrics["requests"],
                "total_errors": user_metrics["errors"],
                "avg_latency_ms": round(avg_latency, 2),
                "status_codes": dict(user_metrics["status_codes"]),
            }
            
            if by_app_hostname:
                result["by_app_hostname"] = by_app_hostname
            if by_container:
                result["by_container"] = by_container
            
            return result

        if app_hostname is not None:
            app_metrics = self.app_hostname_metrics.get(app_hostname, {})
            if not app_metrics:
                return {"error": "No metrics found for this app_hostname"}
            avg_latency = (
                app_metrics["latency_sum"] / app_metrics["latency_count"]
                if app_metrics["latency_count"] > 0
                else 0.0
            )
            result = {
                "app_hostname": app_hostname,
                "total_requests": app_metrics["requests"],
                "total_errors": app_metrics["errors"],
                "avg_latency_ms": round(avg_latency, 2),
                "status_codes": dict(app_metrics["status_codes"]),
            }
            # Include user_id if available
            if app_metrics.get("user_id") is not None:
                result["user_id"] = app_metrics["user_id"]
            return result

        if container_id is not None:
            container_metrics = self.container_metrics.get(container_id, {})
            if not container_metrics:
                return {"error": "No metrics found for this container"}
            avg_latency = (
                container_metrics["latency_sum"] / container_metrics["latency_count"]
                if container_metrics["latency_count"] > 0
                else 0.0
            )
            result = {
                "container_id": container_id,
                "total_requests": container_metrics["requests"],
                "total_errors": container_metrics["errors"],
                "avg_latency_ms": round(avg_latency, 2),
                "status_codes": dict(container_metrics["status_codes"]),
            }
            # Include user_id if available
            if container_metrics.get("user_id") is not None:
                result["user_id"] = container_metrics["user_id"]
            return result

        # Global metrics
        avg_latency = (
            self.latency_sum / self.latency_count if self.latency_count > 0 else 0.0
        )

        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "avg_latency_ms": round(avg_latency, 2),
            "status_codes": dict(self.status_codes),
            "by_user": {
                str(uid): {
                    "requests": metrics["requests"],
                    "errors": metrics["errors"],
                    "avg_latency_ms": round(
                        metrics["latency_sum"] / metrics["latency_count"]
                        if metrics["latency_count"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for uid, metrics in self.user_metrics.items()
            },
            "by_app_hostname": {
                hostname: {
                    "requests": metrics["requests"],
                    "errors": metrics["errors"],
                    "avg_latency_ms": round(
                        metrics["latency_sum"] / metrics["latency_count"]
                        if metrics["latency_count"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for hostname, metrics in self.app_hostname_metrics.items()
            },
            "by_container": {
                cid: {
                    "requests": metrics["requests"],
                    "errors": metrics["errors"],
                    "avg_latency_ms": round(
                        metrics["latency_sum"] / metrics["latency_count"]
                        if metrics["latency_count"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for cid, metrics in self.container_metrics.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics counters."""
        self.total_requests = 0
        self.total_errors = 0
        self.status_codes.clear()
        self.latency_sum = 0.0
        self.latency_count = 0
        self.user_metrics.clear()
        self.app_hostname_metrics.clear()
        self.container_metrics.clear()