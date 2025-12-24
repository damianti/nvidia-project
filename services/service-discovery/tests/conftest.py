"""
Shared fixtures and configuration for service-discovery tests.
"""

import os
import sys
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock
import pytest

from app.schemas.container_data import ContainerEventData
from app.schemas.service_info import ServiceInfo


# Mock external dependencies before importing app modules
sys.modules["confluent_kafka"] = MagicMock()

# Minimal environment variables
os.environ.setdefault("CONSUL_HOST", "http://consul:8500")
os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
os.environ.setdefault("KAFKA_CONSUMER_GROUP", "service-discovery")
os.environ.setdefault("LOG_LEVEL", "INFO")


@pytest.fixture
def sample_container_event() -> Dict[str, Any]:
    """Valid container event for Kafka/Consul tests."""
    return {
        "event": "container.created",
        "container_id": "abc123",
        "container_name": "webapp-1",
        "container_ip": "172.18.0.10",
        "image_id": 1,
        "internal_port": 80,
        "external_port": 32000,
        "app_hostname": "demo.example.com",
        "user_id": 99,
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def container_event_model(sample_container_event: Dict[str, Any]) -> ContainerEventData:
    """Pydantic model built from the container event."""
    return ContainerEventData(**sample_container_event)


@pytest.fixture
def sample_service_info() -> ServiceInfo:
    """ServiceInfo object ready for cache usage."""
    return ServiceInfo(
        container_id="abc123",
        container_ip="172.18.0.10",
        internal_port=80,
        external_port=32000,
        status="passing",
        tags=["image-1", "app-hostname-demo.example.com", "external-port-32000"],
        image_id=1,
        app_hostname="demo.example.com",
    )


@pytest.fixture
def sample_services(sample_service_info: ServiceInfo) -> List[ServiceInfo]:
    """Example list of services."""
    return [sample_service_info]


@pytest.fixture
def mock_async_client_response() -> Mock:
    """Generic mocked httpx response."""
    response = Mock()
    response.status_code = 200
    response.text = "ok"
    response.json.return_value = []
    response.headers = {"X-Consul-Index": "42"}
    return response


@pytest.fixture
def mock_async_client(mock_async_client_response: Mock) -> AsyncMock:
    """Mocked httpx.AsyncClient."""
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    client.put = AsyncMock(return_value=mock_async_client_response)
    client.get = AsyncMock(return_value=mock_async_client_response)
    return client


@pytest.fixture
def mock_httpx(
    monkeypatch: pytest.MonkeyPatch, mock_async_client: AsyncMock
) -> AsyncMock:
    """Patch httpx.AsyncClient to return the mock."""
    import app.services.consul_client as consul_client
    import app.services.consul_watcher as consul_watcher

    monkeypatch.setattr(
        consul_client.httpx, "AsyncClient", lambda timeout=5.0: mock_async_client
    )
    monkeypatch.setattr(
        consul_watcher.httpx, "AsyncClient", lambda timeout=65.0: mock_async_client
    )
    return mock_async_client


@pytest.fixture
def mock_consul_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock consul_client functions for KafkaConsumerService."""
    import app.services.consul_client as consul_client

    mock_module = MagicMock()
    mock_module.register_service = AsyncMock(return_value=True)
    mock_module.deregister_service = AsyncMock(return_value=True)
    monkeypatch.setattr(consul_client, "register_service", mock_module.register_service)
    monkeypatch.setattr(
        consul_client, "deregister_service", mock_module.deregister_service
    )
    return mock_module


@pytest.fixture
def fake_request_with_state() -> Mock:
    """Request with configurable app.state for endpoint tests."""
    req = Mock()
    req.app = SimpleNamespace(state=SimpleNamespace())
    return req
