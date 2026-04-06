"""
Integration tests for load-balancer FastAPI routes.
"""

from contextlib import asynccontextmanager
from typing import List
from unittest.mock import AsyncMock, Mock

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.service_info import ServiceInfo
from app.services.metrics_collector import MetricsCollector


@pytest.fixture
def test_client(sample_service_info: List[ServiceInfo]) -> TestClient:
    """Provide TestClient with injected app.state dependencies."""

    @asynccontextmanager
    async def dummy_lifespan(_):
        yield

    app.router.lifespan_context = lambda _: dummy_lifespan(app)

    discovery_client = Mock()
    discovery_client.get_healthy_services = AsyncMock(return_value=sample_service_info)

    selector = Mock()
    selector.select = AsyncMock(return_value=sample_service_info[0])

    circuit_breaker = Mock()
    circuit_breaker.call = AsyncMock(return_value=sample_service_info)
    circuit_breaker.get_state = AsyncMock(return_value=Mock(value="CLOSED"))

    fallback_cache = Mock()
    fallback_cache.update = AsyncMock()
    fallback_cache.get = AsyncMock(return_value=sample_service_info)

    metrics_collector = Mock()
    metrics_collector.record_request = AsyncMock()
    metrics_collector.update_mapping = AsyncMock()

    app.state.discovery_client = discovery_client
    app.state.service_selector = selector
    app.state.circuit_breaker = circuit_breaker
    app.state.fallback_cache = fallback_cache
    app.state.metrics_collector = metrics_collector

    return TestClient(app)


@pytest.mark.integration
class TestLbRoutesIntegration:
    """Integration coverage for /health and /route endpoints."""

    def test_health_returns_ok(self, test_client: TestClient) -> None:
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_route_happy_path(self, test_client: TestClient) -> None:
        payload = {"app_hostname": "demo.example.com"}

        response = test_client.post("/route", json=payload)

        assert response.status_code == 200
        data = response.json()
        for key in ["target_host", "target_port", "container_id", "image_id", "ttl"]:
            assert key in data

    def test_route_missing_field_returns_400(self, test_client: TestClient) -> None:
        response = test_client.post("/route", json={"wrong": "field"})

        assert response.status_code == 400
        assert "app_hostname" in response.json()["detail"]

    def test_route_empty_hostname_returns_400(self, test_client: TestClient) -> None:
        response = test_client.post("/route", json={"app_hostname": "   "})

        assert response.status_code == 400
        assert "app_hostname" in response.json()["detail"]


@pytest.fixture
def metrics_test_client():
    """
    TestClient with a real MetricsCollector backed by fakeredis.

    Uses a FakeServer shared between a sync client (for pre-populating state
    in synchronous test methods) and an async client (used by MetricsCollector).
    This avoids event-loop conflicts when TestClient runs the ASGI app.
    """

    @asynccontextmanager
    async def dummy_lifespan(_):
        yield

    app.router.lifespan_context = lambda _: dummy_lifespan(app)

    server = fakeredis.aioredis.FakeServer()
    async_redis = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
    sync_redis = fakeredis.FakeRedis(server=server, decode_responses=True)

    real_collector = MetricsCollector(redis=async_redis)
    app.state.metrics_collector = real_collector

    return TestClient(app), sync_redis


@pytest.mark.integration
class TestLbMetricsEndpoints:
    """Integration tests for GET /metrics and GET /metrics/mappings."""

    def test_get_metrics_returns_200_with_empty_state(
        self, metrics_test_client
    ) -> None:
        client, _ = metrics_test_client
        response = client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["total_errors"] == 0
        assert data["avg_latency_ms"] == 0.0
        assert data["status_codes"] == {}

    def test_get_metrics_reflects_recorded_requests(
        self, metrics_test_client
    ) -> None:
        client, sync_redis = metrics_test_client

        # Pre-populate via sync client — same FakeServer, no event-loop conflict.
        sync_redis.hincrby("lb:metrics:global", "total_requests", 2)
        sync_redis.hincrby("lb:metrics:global", "total_errors", 1)
        sync_redis.hincrby("lb:metrics:image:1", "requests", 2)
        sync_redis.hincrby("lb:metrics:image:1", "errors", 1)

        response = client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 2
        assert data["total_errors"] == 1
        assert "by_image" in data
        assert data["by_image"]["1"]["requests"] == 2

    def test_get_mappings_returns_empty_dict_when_no_mappings(
        self, metrics_test_client
    ) -> None:
        client, _ = metrics_test_client
        response = client.get("/metrics/mappings")

        assert response.status_code == 200
        assert response.json() == {"active_mappings": {}}

    def test_get_mappings_reflects_active_mappings(
        self, metrics_test_client
    ) -> None:
        client, sync_redis = metrics_test_client

        sync_redis.hset("lb:metrics:mappings", "myapp", 32100)

        response = client.get("/metrics/mappings")

        assert response.status_code == 200
        data = response.json()
        assert data["active_mappings"]["myapp"] == 32100
