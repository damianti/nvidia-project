"""
Integration tests for load-balancer FastAPI routes.
"""
from contextlib import asynccontextmanager
from typing import List
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.service_info import ServiceInfo


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
    selector.select = Mock(return_value=sample_service_info[0])

    circuit_breaker = Mock()
    circuit_breaker.call = AsyncMock(return_value=sample_service_info)
    circuit_breaker.get_state = Mock(return_value=Mock(value="CLOSED"))

    fallback_cache = Mock()
    fallback_cache.update = AsyncMock()
    fallback_cache.get = AsyncMock(return_value=sample_service_info)

    app.state.discovery_client = discovery_client
    app.state.service_selector = selector
    app.state.circuit_breaker = circuit_breaker
    app.state.fallback_cache = fallback_cache

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
