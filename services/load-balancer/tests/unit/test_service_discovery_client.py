"""
Unit tests for ServiceDiscoveryClient.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, Mock

from app.services.service_discovery_client import ServiceDiscoveryClient, ServiceDiscoveryError
from app.schemas.service_info import ServiceInfo


@pytest.mark.unit
class TestServiceDiscoveryClient:
    """Covers success and error paths using mocked httpx client."""

    @pytest.mark.asyncio
    async def test_get_healthy_services_success(self, monkeypatch: pytest.MonkeyPatch):
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.json.return_value = {"services": [
            {
                "container_id": "abc",
                "container_ip": "10.0.0.1",
                "internal_port": 80,
                "external_port": 30000,
                "status": "passing",
                "tags": [],
                "image_id": 1,
                "app_hostname": "demo",
            }
        ]}
        mock_response.raise_for_status = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)

        monkeypatch.setattr("httpx.AsyncClient", lambda timeout=5.0: mock_client)

        client = ServiceDiscoveryClient(base_url="http://sd")
        services = await client.get_healthy_services(app_hostname="demo")

        assert len(services) == 1
        assert isinstance(services[0], ServiceInfo)
        mock_client.get.assert_awaited_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_healthy_services_http_status_error(self, monkeypatch: pytest.MonkeyPatch):
        mock_client = AsyncMock()
        response = httpx.Response(status_code=500, request=httpx.Request("GET", "http://sd"))
        error = httpx.HTTPStatusError("boom", request=response.request, response=response)
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_client.get = AsyncMock(return_value=mock_response)

        monkeypatch.setattr("httpx.AsyncClient", lambda timeout=5.0: mock_client)

        client = ServiceDiscoveryClient(base_url="http://sd")

        with pytest.raises(ServiceDiscoveryError):
            await client.get_healthy_services(app_hostname="demo")

    @pytest.mark.asyncio
    async def test_get_healthy_services_http_error(self, monkeypatch: pytest.MonkeyPatch):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("network"))

        monkeypatch.setattr("httpx.AsyncClient", lambda timeout=5.0: mock_client)

        client = ServiceDiscoveryClient(base_url="http://sd")

        with pytest.raises(ServiceDiscoveryError):
            await client.get_healthy_services(app_hostname="demo")
