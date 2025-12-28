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

        self.image_metrics: Dict[int, Dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "errors": 0,
                "status_codes": defaultdict(int),
                "latency_sum": 0.0,
                "latency_count": 0,
            }
        )

        self.active_mappings: Dict[str, int] = {}


    def record_request(self,
        status_code: int,
        latency_ms: float = 0.0,
        image_id: int = None,
        app_hostname: str = None,
        traffic_bytes: int = 0
        ) -> None:
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

        if image_id is not None:
            img_metrics = self.image_metrics[image_id]
            img_metrics["requests"] += 1
            img_metrics["status_codes"][str(status_code)] += 1
            
            if status_code >= 400:
                img_metrics["errors"] += 1
                
            if latency_ms > 0:
                img_metrics["latency_sum"] += latency_ms
                img_metrics["latency_count"] += 1

        if app_hostname:
            host_metrics = self.hostname_metrics[app_hostname]
            host_metrics["requests"] += 1
            host_metrics["traffic"] += traffic_bytes
            host_metrics["status_codes"][str(status_code)] += 1
            
            if status_code >= 400:
                host_metrics["errors"] += 1
    
    def update_mapping(self, app_hostname: str, external_port: int) -> None:
        """
        Update the active mapping for an app hostname.
        
        Args:
            app_hostname: Application hostname
            external_port: External port number
        """
        self.active_mappings[app_hostname] = external_port
    
    def remove_mapping(self, app_hostname: str) -> None:
        """
        Remove the mapping for an app hostname.
        
        Args:
            app_hostname: Application hostname to remove
        """
        self.active_mappings.pop(app_hostname, None)

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
