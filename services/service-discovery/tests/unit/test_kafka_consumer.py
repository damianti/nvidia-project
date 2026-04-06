"""
Unit tests for KafkaConsumerService.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from app.schemas.container_data import ContainerEventData
from app.services.kafka_consumer import KafkaConsumerService


@pytest.mark.unit
class TestKafkaConsumerService:
    """Kafka event processing tests."""

    @pytest.mark.asyncio
    async def test_process_message_registra_con_exito(
        self, sample_container_event: dict, mock_consul_client
    ) -> None:
        """Processes container.created and updates counters."""
        service = KafkaConsumerService()
        message = Mock()
        message.value.return_value = json.dumps(sample_container_event).encode()

        await service.process_message(message)

        assert service.message_count == 1
        assert service.registration_success == 1
        assert service.registration_failures == 0
        mock_consul_client.register_service.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_message_registro_fallido(
        self, sample_container_event: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If registration fails, increases registration_failures."""
        service = KafkaConsumerService()
        message = Mock()
        message.value.return_value = json.dumps(sample_container_event).encode()

        async def fail_register(_):
            return False

        import app.services.consul_client as consul_client

        monkeypatch.setattr(
            consul_client, "register_service", AsyncMock(side_effect=fail_register)
        )

        await service.process_message(message)

        assert service.message_count == 1
        assert service.registration_failures == 1

    @pytest.mark.asyncio
    async def test_process_message_json_invalido(self) -> None:
        """Handles invalid JSON without raising."""
        service = KafkaConsumerService()
        message = Mock()
        message.value.return_value = b"{invalid json"

        await service.process_message(message)

        assert service.message_count == 0

    @pytest.mark.asyncio
    async def test_process_message_validation_error(
        self, sample_container_event: dict
    ) -> None:
        """Handles pydantic validation errors."""
        service = KafkaConsumerService()
        message = Mock()
        invalid = dict(sample_container_event)
        invalid["image_id"] = "not-int"
        message.value.return_value = json.dumps(invalid).encode()

        await service.process_message(message)

        assert service.message_count == 0

    @pytest.mark.asyncio
    async def test_process_message_evento_desconocido(
        self, sample_container_event: dict
    ) -> None:
        """Unknown events should not break processing."""
        service = KafkaConsumerService()
        message = Mock()
        data = dict(sample_container_event)
        data["event"] = "other.event"
        message.value.return_value = json.dumps(data).encode()

        await service.process_message(message)

        assert service.message_count == 0

    @pytest.mark.asyncio
    async def test_start_inicia_consumidor_y_sale_con_keyboardinterrupt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Covers start loop interrupted to close gracefully."""

        # Fake Consumer con poll que levanta KeyboardInterrupt en segunda llamada
        class FakeConsumer:
            def __init__(self):
                self.closed = False
                self.poll_calls = 0

            def subscribe(self, topics):
                self.topics = topics

            def poll(self, timeout):
                self.poll_calls += 1
                if self.poll_calls > 1:
                    raise KeyboardInterrupt()
                return None

            def close(self):
                self.closed = True

        fake_consumer = FakeConsumer()

        async def fake_to_thread(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        monkeypatch.setattr(
            "app.services.kafka_consumer.Consumer", lambda config: fake_consumer
        )
        monkeypatch.setattr("asyncio.to_thread", fake_to_thread)

        service = KafkaConsumerService()

        # Limitar ejecución a pocas iteraciones usando asyncio.wait_for
        await asyncio.wait_for(service.start(), timeout=1.0)

        assert service.running is False
        assert fake_consumer.topics == ["container-lifecycle"]


@pytest.fixture
def image_event_data() -> ContainerEventData:
    """
    ContainerEventData used as a stand-in for image lifecycle events.

    NOTE: The current schema only validates container.* events.  We use a
    container.deleted payload here so Pydantic accepts it; image_id is the only
    field _on_image_deleted() actually reads.  This is intentional — fixing the
    schema to accept 'image.deleted' natively is tracked as a separate task.
    """
    return ContainerEventData(
        event="container.deleted",
        container_id="abc123",
        container_name="webapp-1",
        container_ip="172.18.0.10",
        image_id=42,
        internal_port=80,
        external_port=32000,
        app_hostname="myapp",
        user_id=1,
        timestamp=datetime.utcnow(),
    )


@pytest.mark.unit
class TestOnImageDeleted:
    """Unit tests for _on_image_deleted() handler."""

    @pytest.mark.asyncio
    async def test_deregisters_all_services_for_image(
        self,
        image_event_data: ContainerEventData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Deregisters every Consul service tagged with image-{image_id}."""
        import app.services.consul_client as consul_client

        mock_services = [
            {"container_id": "ctr-1"},
            {"container_id": "ctr-2"},
        ]
        monkeypatch.setattr(
            consul_client,
            "query_healthy_services",
            AsyncMock(return_value=mock_services),
        )
        mock_deregister = AsyncMock(return_value=True)
        monkeypatch.setattr(consul_client, "deregister_service", mock_deregister)

        service = KafkaConsumerService()
        await service._on_image_deleted(image_event_data)

        consul_client.query_healthy_services.assert_awaited_once_with(
            tags=["image-42"]
        )
        assert mock_deregister.await_count == 2
        mock_deregister.assert_any_await("ctr-1")
        mock_deregister.assert_any_await("ctr-2")

    @pytest.mark.asyncio
    async def test_no_services_registered_is_a_noop(
        self,
        image_event_data: ContainerEventData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When Consul returns no services for the image, deregister is never called."""
        import app.services.consul_client as consul_client

        monkeypatch.setattr(
            consul_client,
            "query_healthy_services",
            AsyncMock(return_value=[]),
        )
        mock_deregister = AsyncMock()
        monkeypatch.setattr(consul_client, "deregister_service", mock_deregister)

        service = KafkaConsumerService()
        await service._on_image_deleted(image_event_data)

        mock_deregister.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_deregistration_failure_is_logged_and_continues(
        self,
        image_event_data: ContainerEventData,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A failed deregistration does not abort processing of remaining services."""
        import app.services.consul_client as consul_client

        mock_services = [
            {"container_id": "ctr-fail"},
            {"container_id": "ctr-ok"},
        ]
        monkeypatch.setattr(
            consul_client,
            "query_healthy_services",
            AsyncMock(return_value=mock_services),
        )
        # First call fails, second succeeds
        mock_deregister = AsyncMock(side_effect=[False, True])
        monkeypatch.setattr(consul_client, "deregister_service", mock_deregister)

        service = KafkaConsumerService()
        await service._on_image_deleted(image_event_data)

        # Both containers were attempted regardless of the first failure
        assert mock_deregister.await_count == 2
