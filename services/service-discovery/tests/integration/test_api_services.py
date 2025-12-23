"""
Integration tests for service-discovery endpoints.
"""
from datetime import datetime
from typing import List
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

from app.main import app
from app.services.service_cache import ServiceCache
from app.schemas.service_info import ServiceInfo
from app.services.kafka_consumer import KafkaConsumerService


class TestApiServicesIntegration:
    """Tests for /services endpoints and metrics."""

    @pytest.fixture(autouse=True)
    def setup_app_state(self, sample_services: List[ServiceInfo]) -> None:
        """Configure app.state without running lifespan."""
        @asynccontextmanager
        async def dummy_lifespan(_):
            yield

        app.router.lifespan_context = lambda _: dummy_lifespan(app)

        cache = ServiceCache()
        cache._last_update = datetime.utcnow()
        cache._cache = {svc.image_id: [svc] for svc in sample_services if svc.image_id}
        for svc in sample_services:
            if svc.app_hostname and svc.image_id:
                cache._app_hostname_map.add(svc.app_hostname, svc.image_id)

        app.state.service_cache = cache

        consumer = KafkaConsumerService()
        consumer.message_count = 5
        consumer.registration_success = 4
        consumer.registration_failures = 1
        app.state.kafka_consumer = consumer

        yield

        if hasattr(app.state, "service_cache"):
            del app.state.service_cache
        if hasattr(app.state, "kafka_consumer"):
            del app.state.kafka_consumer

    def test_get_healthy_services_happy_path(self, sample_services: List[ServiceInfo]) -> None:
        """Returns services from cache."""
        with TestClient(app) as client:
            response = client.get("/services/healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(sample_services)
        assert data["services"][0]["container_id"] == sample_services[0].container_id

    def test_get_healthy_services_filtrado_hostname(self, sample_services: List[ServiceInfo]) -> None:
        """Filters by app_hostname using mapping."""
        with TestClient(app) as client:
            response = client.get("/services/healthy", params={"app_hostname": "demo.example.com"})

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["services"][0]["app_hostname"] == "demo.example.com"

    def test_get_healthy_services_cache_no_inicializado(self) -> None:
        """Returns 503 if cache has no last_update."""
        app.state.service_cache._last_update = None
        with TestClient(app) as client:
            response = client.get("/services/healthy")

        assert response.status_code == 503
        assert "cache not yet initialized" in response.json()["detail"].lower()

    def test_get_cache_status(self) -> None:
        """Returns cache statistics."""
        with TestClient(app) as client:
            response = client.get("/services/cache/status")

        assert response.status_code == 200
        data = response.json()
        assert "last_index" in data
        assert "total_services" in data

    def test_metrics_endpoint(self) -> None:
        """Metrics reflect consumer counters."""
        with TestClient(app) as client:
            response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["messages_processed"] == 5
        assert data["registration_success"] == 4
        assert data["registration_failures"] == 1
