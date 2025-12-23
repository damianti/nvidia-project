"""
Unit tests for FallbackCache.
"""
import asyncio
import pytest
from datetime import datetime, timedelta

from app.services.fallback_cache import FallbackCache
from app.schemas.service_info import ServiceInfo


@pytest.mark.unit
class TestFallbackCache:
    """Tests for fallback cache with TTL and normalization."""

    @pytest.mark.asyncio
    async def test_update_and_get_hit(self, sample_service_info):
        cache = FallbackCache(ttl_seconds=5.0)

        await cache.update("Example.com", sample_service_info)
        result = await cache.get("example.com")

        assert result == sample_service_info
        status = cache.get_status()
        assert status["entries_count"] == 1
        assert "example.com" in status["entries"]

    @pytest.mark.asyncio
    async def test_get_miss_when_not_found(self):
        cache = FallbackCache(ttl_seconds=1.0)

        result = await cache.get("missing.example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self, sample_service_info):
        cache = FallbackCache(ttl_seconds=0.01)
        await cache.update("demo.example.com", sample_service_info)
        await asyncio.sleep(0.05)

        result = await cache.get("demo.example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_removes_entries(self, sample_service_info):
        cache = FallbackCache(ttl_seconds=5.0)
        await cache.update("demo", sample_service_info)

        await cache.clear()
        status = cache.get_status()

        assert status["entries_count"] == 0

    @pytest.mark.asyncio
    async def test_normalizes_hostname_variations(self, sample_service_info):
        cache = FallbackCache(ttl_seconds=5.0)
        await cache.update("HTTP://Demo.Example.com:8080/path", sample_service_info)

        result = await cache.get("demo.example.com")

        assert result == sample_service_info
