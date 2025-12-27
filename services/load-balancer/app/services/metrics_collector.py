"""
Metrics Collector for Load Balancer.

Tracks request metrics, latency, and port mappings for monitoring and analytics.
"""

import logging
from typing import Dict, Any
from collections import defaultdict

from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)


class MetricsCollector:
    """Collects and aggregates metrics for the load balancer."""

    def __init__(self):
        """Initialize metrics collector with empty counters."""
        self.total_requests = 0
        self.total_errors = 0
        self.status_codes: Dict[str, int] = defaultdict(int)
        self.latency_sum = 0.0
        self.latency_count = 0

    def record_request(self, status_code: int, latency_ms: float = 0.0) -> None:
        """
        Record a request with its status code and latency.

        Args:
            status_code: HTTP status code of the response
            latency_ms: Request latency in milliseconds
        """
        self.total_requests += 1
        self.status_codes[str(status_code)] += 1

        if status_code >= 400:
            self.total_errors += 1

        if latency_ms > 0:
            self.latency_sum += latency_ms
            self.latency_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.

        Returns:
            Dictionary containing:
            - total_requests: Total number of requests processed
            - total_errors: Total number of error responses (4xx, 5xx)
            - avg_latency_ms: Average latency in milliseconds
            - status_codes: Dictionary mapping status codes to counts
        """
        avg_latency = (
            self.latency_sum / self.latency_count if self.latency_count > 0 else 0.0
        )

        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "avg_latency_ms": round(avg_latency, 2),
            "status_codes": dict(self.status_codes),
        }

    def reset(self) -> None:
        """Reset all metrics counters."""
        self.total_requests = 0
        self.total_errors = 0
        self.status_codes.clear()
        self.latency_sum = 0.0
        self.latency_count = 0
