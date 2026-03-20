"""
Unit tests for FallbackCache.
"""

import asyncio
import pytest
import pytest_asyncio

import fakeredis.aioredis

from app.services.fallback_cache import FallbackCache


@pytest_asyncio.fixture
async def cache() -> FallbackCache:
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return FallbackCache(redis=r, ttl_seconds=5.0)


@pytest.mark.unit
class TestFallbackCache:
    """Tests for fallback cache with TTL and normalization."""

    @pytest.mark.asyncio
    async def test_update_and_get_hit(self, cache: FallbackCache, sample_service_info):
        await cache.update("Example.com", sample_service_info)
        result = await cache.get("example.com")

        assert result == sample_service_info
        status = await cache.get_status()
        assert status["entries_count"] == 1

    @pytest.mark.asyncio
    async def test_get_miss_when_not_found(self, cache: FallbackCache):
        result = await cache.get("missing.example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(
        self, sample_service_info, fake_redis
    ):
        short_cache = FallbackCache(redis=fake_redis, ttl_seconds=1)
        await short_cache.update("demo.example.com", sample_service_info)
        await asyncio.sleep(1.1)

        result = await short_cache.get("demo.example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_removes_entries(self, cache: FallbackCache, sample_service_info):
        await cache.update("demo", sample_service_info)

        await cache.clear()
        status = await cache.get_status()

        assert status["entries_count"] == 0

    @pytest.mark.asyncio
    async def test_normalizes_hostname_variations(
        self, cache: FallbackCache, sample_service_info
    ):
        await cache.update("HTTP://Demo.Example.com:8080/path", sample_service_info)

        result = await cache.get("demo.example.com")

        assert result == sample_service_info
