"""
Unit tests for ServiceCache.
"""

import pytest
from datetime import datetime
from typing import List

from app.services.service_cache import ServiceCache
from app.services.website_mapping import AppHostnameMapping
from app.schemas.service_info import ServiceInfo


class TestServiceCache:
    """ServiceCache tests using AAA pattern."""

    @pytest.mark.asyncio
    async def test_update_services_reemplaza_cache(
        self, sample_services: List[ServiceInfo], sample_service_info: ServiceInfo
    ) -> None:
        """Replaces cache contents and clears previous data."""
        cache = ServiceCache()
        viejo = ServiceInfo(
            container_id="old",
            container_ip="10.0.0.1",
            internal_port=80,
            external_port=30000,
            status="passing",
            tags=["image-2"],
            image_id=2,
            app_hostname="old.example.com",
        )
        await cache.update_services([viejo], index=1)

        await cache.update_services(sample_services, index=5)

        assert cache.get_services(image_id=1) == sample_services
        assert cache.get_services(image_id=2) == []
        status = cache.get_cache_status()
        assert status["last_index"] == 5
        assert status["total_services"] == 1

    @pytest.mark.asyncio
    async def test_update_services_mapea_app_hostname(
        self, sample_service_info: ServiceInfo
    ) -> None:
        """Adds app_hostname -> image_id mapping."""
        mapping = AppHostnameMapping()
        cache = ServiceCache(mapping)

        await cache.update_services([sample_service_info], index=10)

        servicios = cache.get_services(app_hostname="demo.example.com")
        assert len(servicios) == 1
        assert servicios[0].image_id == 1
        assert mapping.get_image_id("demo.example.com") == 1

    def test_get_services_sin_filtros(self, sample_services: List[ServiceInfo]) -> None:
        """Returns all services when no filters are provided."""
        cache = ServiceCache()
        cache._cache = {1: sample_services}

        servicios = cache.get_services()

        assert servicios == sample_services

    def test_get_services_app_hostname_invalido(self) -> None:
        """Returns empty list when hostname does not exist."""
        cache = ServiceCache()

        servicios = cache.get_services(app_hostname="nope.example.com")

        assert servicios == []

    def test_get_cache_status_retorna_estadisticas(self) -> None:
        """Returns basic cache metrics."""
        cache = ServiceCache()
        cache._last_index = 7
        cache._last_update = datetime(2025, 1, 1)
        cache._cache = {1: [], 2: []}

        status = cache.get_cache_status()

        assert status["last_index"] == 7
        assert status["last_update"].startswith("2025-01-01")
        assert status["total_services"] == 0
        assert status["image_ids"] == [1, 2]
