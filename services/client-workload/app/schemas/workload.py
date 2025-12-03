from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class WorkloadPattern(str, Enum):
    """Load testing patterns"""
    CONSTANT = "constant"  # Constant RPS
    SPIKE = "spike"  # Sudden spike
    GRADUAL = "gradual"  # Gradual increase
    WAVE = "wave"  # Wave pattern


class WorkloadRequest(BaseModel):
    """Request to start a workload test"""
    website_urls: Optional[List[str]] = Field(
        None,
        description="Specific website URLs to test. If None, uses all available services"
    )
    rps: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Requests per second"
    )
    duration_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Test duration in seconds"
    )
    pattern: WorkloadPattern = Field(
        default=WorkloadPattern.CONSTANT,
        description="Load pattern"
    )
    use_load_balancer: bool = Field(
        default=True,
        description="Use Load Balancer (True) or direct container access (False)"
    )


class RequestMetrics(BaseModel):
    """Metrics for a single request"""
    timestamp: float
    website_url: str
    status_code: Optional[int]
    latency_ms: float
    error: Optional[str]


class WorkloadMetrics(BaseModel):
    """Aggregated metrics for a workload test"""
    test_id: str
    status: str  # running, completed, stopped
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    error_rate: float
    start_time: float
    end_time: Optional[float]
    duration_seconds: float
    website_urls: List[str]
    status_code_distribution: dict


class WorkloadStatus(BaseModel):
    """Current status of a workload test"""
    test_id: str
    status: str
    config: WorkloadRequest
    metrics: Optional[WorkloadMetrics] = None

