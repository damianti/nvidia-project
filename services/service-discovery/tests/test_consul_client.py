"""
Unit tests for consul_client.
"""

import pytest
from unittest.mock import AsyncMock

from app.services import consul_client
from app.schemas.container_data import ContainerEventData


@pytest.mark.unit
class TestConsulClient:
    """Registration, deregistration and query tests for Consul."""

    @pytest.mark.asyncio
    async def test_register_service_exito(
        self, container_event_model: ContainerEventData, mock_httpx
    ) -> None:
        """Successful register returns True and hits endpoint."""
        mock_httpx.put.return_value.status_code = 200

        result = await consul_client.register_service(container_event_model)

        assert result is True
        mock_httpx.put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_service_falla_status(
        self, container_event_model: ContainerEventData, mock_httpx
    ) -> None:
        """Non-200 response returns False."""
        mock_httpx.put.return_value.status_code = 500

        result = await consul_client.register_service(container_event_model)

        assert result is False
        mock_httpx.put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_service_excepcion(
        self, container_event_model: ContainerEventData, mock_httpx
    ) -> None:
        """Exceptions return False without raising."""
        mock_httpx.put = AsyncMock(side_effect=Exception("boom"))

        result = await consul_client.register_service(container_event_model)

        assert result is False

    @pytest.mark.asyncio
    async def test_deregister_service_exito(self, mock_httpx) -> None:
        """Successful deregister returns True."""
        mock_httpx.put.return_value.status_code = 200

        result = await consul_client.deregister_service("abc123")

        assert result is True
        mock_httpx.put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deregister_service_falla(self, mock_httpx) -> None:
        """Deregister error returns False."""
        mock_httpx.put.return_value.status_code = 404

        result = await consul_client.deregister_service("abc123")

        assert result is False

    @pytest.mark.asyncio
    async def test_query_healthy_services_sin_tags(self, mock_httpx) -> None:
        """Query without tags returns empty list when response empty."""
        mock_httpx.get.return_value.json.return_value = []

        servicios = await consul_client.query_healthy_services()

        assert servicios == []
        mock_httpx.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_query_healthy_services_con_tags(self, mock_httpx) -> None:
        """Query with tags calls once per tag."""
        mock_httpx.get.return_value.json.return_value = []

        servicios = await consul_client.query_healthy_services(tags=["a", "b"])

        assert servicios == []
        assert mock_httpx.get.await_count == 2

    @pytest.mark.asyncio
    async def test_query_healthy_services_excepcion(
        self, mock_httpx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exception during request returns empty list."""

        async def raise_error(*_, **__):
            raise Exception("boom")

        mock_httpx.get = AsyncMock(side_effect=raise_error)

        servicios = await consul_client.query_healthy_services(
            service_name="webapp-service"
        )

        assert servicios == []

    @pytest.mark.asyncio
    async def test_deregister_service_excepcion(
        self, mock_httpx, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exception in deregister returns False without raising."""
        mock_httpx.put = AsyncMock(side_effect=Exception("boom"))

        result = await consul_client.deregister_service("abc123")

        assert result is False
