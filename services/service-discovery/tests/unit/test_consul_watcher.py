"""
Unit tests for ConsulWatcher.
"""
import pytest
from unittest.mock import AsyncMock

from app.services.consul_watcher import ConsulWatcher
from app.services.service_cache import ServiceCache


@pytest.mark.unit
class TestConsulWatcher:
    """Consul watcher tests."""

    def test_parse_services_extrae_campos(self) -> None:
        """Parses Consul response into ServiceInfo filtering passing checks."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)

        datos = [
            {
                "Service": {
                    "ID": "abc123",
                    "Address": "172.18.0.10",
                    "Port": 80,
                    "Tags": ["image-1", "app-hostname-demo.example.com", "external-port-32000"],
                },
                "Checks": [{"Status": "passing"}],
            },
            {
                "Service": {
                    "ID": "skip",
                    "Address": "172.18.0.11",
                    "Port": 81,
                    "Tags": [],
                },
                "Checks": [{"Status": "critical"}],
            },
        ]

        servicios = watcher._parse_services(datos)

        assert len(servicios) == 1
        svc = servicios[0]
        assert svc.container_id == "abc123"
        assert svc.image_id == 1
        assert svc.app_hostname == "demo.example.com"
        assert svc.external_port == 32000

    @pytest.mark.asyncio
    async def test_watch_loop_actualiza_cache(self, mock_httpx) -> None:
        """_watch_loop updates cache and last_index on 200 response."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)
        mock_httpx.get.return_value.status_code = 200
        mock_httpx.get.return_value.json.return_value = []
        mock_httpx.get.return_value.headers = {"X-Consul-Index": "99"}

        await watcher._watch_loop()

        assert cache.get_cache_status()["last_index"] == 99
        mock_httpx.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_watch_loop_404_vacia_cache(self, mock_httpx) -> None:
        """If Consul returns 404, cache is cleared."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)
        mock_httpx.get.return_value.status_code = 404
        mock_httpx.get.return_value.json.return_value = []
        mock_httpx.get.return_value.headers = {"X-Consul-Index": "0"}

        await watcher._watch_loop()

        assert cache.get_cache_status()["total_services"] == 0

    def test_extract_helpers(self) -> None:
        """Extracts image_id, app_hostname and external_port from tags."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)
        tags = ["image-3", "app-hostname-MyApp.com", "external-port-31000"]

        assert watcher._extract_image_id(tags) == 3
        assert watcher._extract_app_hostname(tags) == "MyApp.com"
        assert watcher._extract_external_port(tags) == 31000

    def test_extract_image_id_invalido(self) -> None:
        """Tags without image return None safely."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)

        assert watcher._extract_image_id(["other-tag"]) is None

    @pytest.mark.asyncio
    async def test_start_ejecuta_watch_loop_y_stop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Covers start loop setting running False after one iteration."""
        cache = ServiceCache()
        watcher = ConsulWatcher(cache)
        called = {"count": 0}

        async def fake_watch_loop():
            called["count"] += 1
            watcher.running = False

        monkeypatch.setattr(watcher, "_watch_loop", fake_watch_loop)

        await watcher.start()

        assert called["count"] == 1
        assert watcher.running is False
