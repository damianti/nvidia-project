"""
Unit tests for lb_service helpers and request handling.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException

from app.services import lb_service
from app.services.lb_service import (
    normalize_app_hostname,
    handle_request,
    _pick_service,
)
from app.schemas.service_info import ServiceInfo
from app.services.circuit_breaker import CircuitBreakerOpenError
from app.services.service_discovery_client import ServiceDiscoveryError


@pytest.mark.unit
class TestNormalizeHostname:
    """Hostname normalization tests."""

    def test_strips_protocol_and_port(self):
        assert (
            normalize_app_hostname("https://Demo.Example.com:8080/path")
            == "demo.example.com"
        )

    def test_returns_empty_on_blank(self):
        assert normalize_app_hostname("   ") == ""


@pytest.mark.unit
class TestPickService:
    """Tests for _pick_service selection logic."""

    @pytest.mark.asyncio
    async def test_success_updates_fallback(
        self, mock_discovery_client, mock_circuit_breaker, mock_fallback_cache
    ):
        service = ServiceInfo(
            container_id="a",
            container_ip="1.1.1.1",
            internal_port=80,
            external_port=30000,
            status="passing",
            image_id=1,
            app_hostname="demo",
        )
        mock_circuit_breaker.call.return_value = [service]

        result = await _pick_service(
            app_hostname="demo",
            discovery_client=mock_discovery_client,
            selector=Mock(select=Mock(return_value=service)),
            circuit_breaker=mock_circuit_breaker,
            fallback_cache=mock_fallback_cache,
        )

        assert result == service
        mock_fallback_cache.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_circuit_open_uses_fallback(self, mock_fallback_cache):
        mock_cb = Mock()
        mock_cb.call = AsyncMock(side_effect=CircuitBreakerOpenError())
        mock_cb.get_state = Mock(return_value=Mock(value="OPEN"))

        service = ServiceInfo(
            container_id="a",
            container_ip="1.1.1.1",
            internal_port=80,
            external_port=30000,
            status="passing",
            image_id=1,
            app_hostname="demo",
        )
        mock_fallback_cache.get = AsyncMock(return_value=[service])

        result = await _pick_service(
            app_hostname="demo",
            discovery_client=Mock(),
            selector=Mock(select=Mock(return_value=service)),
            circuit_breaker=mock_cb,
            fallback_cache=mock_fallback_cache,
        )

        assert result == service

    @pytest.mark.asyncio
    async def test_discovery_error_no_fallback_raises(self, mock_fallback_cache):
        mock_cb = Mock()
        mock_cb.call = AsyncMock(side_effect=ServiceDiscoveryError("down"))
        mock_cb.get_state = Mock(return_value=Mock(value="CLOSED"))
        mock_fallback_cache.get = AsyncMock(return_value=None)

        with pytest.raises(ServiceDiscoveryError):
            await _pick_service(
                app_hostname="demo",
                discovery_client=Mock(),
                selector=Mock(select=Mock(return_value=None)),
                circuit_breaker=mock_cb,
                fallback_cache=mock_fallback_cache,
            )

    @pytest.mark.asyncio
    async def test_no_services_returns_none(
        self, mock_circuit_breaker, mock_fallback_cache
    ):
        mock_circuit_breaker.call.return_value = []
        mock_fallback_cache.get = AsyncMock(return_value=None)

        result = await _pick_service(
            app_hostname="demo",
            discovery_client=Mock(),
            selector=Mock(select=Mock(return_value=None)),
            circuit_breaker=mock_circuit_breaker,
            fallback_cache=mock_fallback_cache,
        )

        assert result is None


@pytest.mark.unit
class TestHandleRequest:
    """Tests for handle_request validation and happy path."""

    @pytest.mark.asyncio
    async def test_handle_request_success(self, dummy_request_factory):
        service = ServiceInfo(
            container_id="a",
            container_ip="1.1.1.1",
            internal_port=80,
            external_port=30000,
            status="passing",
            image_id=1,
            app_hostname="demo",
        )
        request = dummy_request_factory({"app_hostname": "Demo.Example.com"})

        original_pick = lb_service._pick_service
        lb_service._pick_service = AsyncMock(return_value=service)

        result = await handle_request(
            request=request,
            discovery_client=Mock(),
            selector=Mock(),
            circuit_breaker=Mock(get_state=Mock(return_value=Mock(value="CLOSED"))),
            fallback_cache=Mock(),
        )

        assert result["target_host"]
        assert result["target_port"] == 30000
        assert result["container_id"] == "a"
        assert result["image_id"] == 1
        lb_service._pick_service = original_pick

    @pytest.mark.asyncio
    async def test_handle_request_missing_body(self, dummy_request_factory):
        request = dummy_request_factory(None)

        with pytest.raises(HTTPException) as exc:
            await handle_request(
                request=request,
                discovery_client=Mock(),
                selector=Mock(),
                circuit_breaker=Mock(),
                fallback_cache=Mock(),
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_request_missing_app_hostname(self, dummy_request_factory):
        request = dummy_request_factory({"foo": "bar"})

        with pytest.raises(HTTPException) as exc:
            await handle_request(
                request=request,
                discovery_client=Mock(),
                selector=Mock(),
                circuit_breaker=Mock(),
                fallback_cache=Mock(),
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_request_empty_hostname(self, dummy_request_factory):
        request = dummy_request_factory({"app_hostname": "   "})

        with pytest.raises(HTTPException) as exc:
            await handle_request(
                request=request,
                discovery_client=Mock(),
                selector=Mock(),
                circuit_breaker=Mock(),
                fallback_cache=Mock(),
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_request_invalid_json(self):
        request = Mock()
        request.body = AsyncMock(side_effect=json.JSONDecodeError("bad", "x", 0))

        with pytest.raises(HTTPException) as exc:
            await handle_request(
                request=request,
                discovery_client=Mock(),
                selector=Mock(),
                circuit_breaker=Mock(),
                fallback_cache=Mock(),
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handle_request_service_discovery_error(self, dummy_request_factory):
        request = dummy_request_factory({"app_hostname": "demo"})
        mock_cb = Mock()
        mock_cb.get_state = Mock(return_value=Mock(value="OPEN"))
        mock_cb.call = AsyncMock(side_effect=ServiceDiscoveryError("down"))
        fallback = Mock()
        fallback.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await handle_request(
                request=request,
                discovery_client=Mock(),
                selector=Mock(),
                circuit_breaker=mock_cb,
                fallback_cache=fallback,
            )
        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_handle_request_no_service_available(self, dummy_request_factory):
        request = dummy_request_factory({"app_hostname": "demo"})

        # Patch _pick_service to return None via monkeypatching attribute
        async def pick_none(**_):
            return None

        original_pick = lb_service._pick_service
        lb_service._pick_service = AsyncMock(return_value=None)
        try:
            with pytest.raises(HTTPException) as exc:
                await handle_request(
                    request=request,
                    discovery_client=Mock(),
                    selector=Mock(),
                    circuit_breaker=Mock(),
                    fallback_cache=Mock(),
                )
            assert exc.value.status_code == 503
        finally:
            lb_service._pick_service = original_pick
