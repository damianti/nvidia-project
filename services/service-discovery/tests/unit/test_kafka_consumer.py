"""
Unit tests for KafkaConsumerService.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, Mock

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
