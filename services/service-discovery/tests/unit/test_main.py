"""
Unit tests for app.main (lifespan and basic setup).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.main import app, lifespan


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lifespan_inicia_y_detiene_tareas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify lifespan starts and stops tasks without errors."""
    # Service mocks
    mock_kafka = MagicMock()
    mock_watcher = MagicMock()
    mock_kafka.start = AsyncMock()
    mock_watcher.start = AsyncMock()
    mock_kafka.stop = MagicMock()
    mock_watcher.stop = MagicMock()

    # Patch classes to return mocks
    # KafkaConsumerService and ConsulWatcher are imported in app.core.lifespan
    import app.core.lifespan as lifespan_module

    monkeypatch.setattr(lifespan_module, "KafkaConsumerService", lambda: mock_kafka)
    monkeypatch.setattr(lifespan_module, "ConsulWatcher", lambda cache: mock_watcher)

    async def fake_wait_for(task, timeout):
        raise asyncio.TimeoutError()

    monkeypatch.setattr("asyncio.wait_for", fake_wait_for)

    async with lifespan(app):
        assert hasattr(app.state, "kafka_task")
        assert hasattr(app.state, "watcher_task")

    # stop should be called even when TimeoutError happens
    mock_kafka.stop.assert_called_once()
    mock_watcher.stop.assert_called_once()
