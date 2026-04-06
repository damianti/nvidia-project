"""
Unit tests for MetricsCollector.

Verifies that request metrics and hostname mappings are correctly
written to and read from Redis.
"""

import pytest
import pytest_asyncio
import fakeredis.aioredis

from app.services.metrics_collector import MetricsCollector


@pytest_asyncio.fixture
async def collector() -> MetricsCollector:
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return MetricsCollector(redis=r)


@pytest.mark.unit
class TestRecordRequest:
    """Tests for record_request() counter updates."""

    @pytest.mark.asyncio
    async def test_increments_total_requests(self, collector: MetricsCollector) -> None:
        await collector.record_request(status_code=200)
        await collector.record_request(status_code=200)

        metrics = await collector.get_metrics()

        assert metrics["total_requests"] == 2

    @pytest.mark.asyncio
    async def test_increments_total_errors_on_4xx_5xx(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=404)
        await collector.record_request(status_code=500)
        await collector.record_request(status_code=200)

        metrics = await collector.get_metrics()

        assert metrics["total_errors"] == 2

    @pytest.mark.asyncio
    async def test_tracks_status_code_breakdown(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=200)
        await collector.record_request(status_code=200)
        await collector.record_request(status_code=404)

        metrics = await collector.get_metrics()

        assert metrics["status_codes"]["200"] == 2
        assert metrics["status_codes"]["404"] == 1

    @pytest.mark.asyncio
    async def test_calculates_avg_latency(self, collector: MetricsCollector) -> None:
        await collector.record_request(status_code=200, latency_ms=100.0)
        await collector.record_request(status_code=200, latency_ms=200.0)

        metrics = await collector.get_metrics()

        assert metrics["avg_latency_ms"] == 150.0

    @pytest.mark.asyncio
    async def test_zero_latency_not_counted_in_average(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=200, latency_ms=0.0)

        metrics = await collector.get_metrics()

        assert metrics["avg_latency_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_tracks_per_image_metrics(self, collector: MetricsCollector) -> None:
        await collector.record_request(status_code=200, latency_ms=50.0, image_id=42)
        await collector.record_request(status_code=500, image_id=42)

        metrics = await collector.get_metrics()

        image_stats = metrics["by_image"]["42"]
        assert image_stats["requests"] == 2
        assert image_stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_tracks_per_hostname_metrics(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(
            status_code=200,
            latency_ms=30.0,
            app_hostname="myapp",
            traffic_bytes=1024,
        )
        await collector.record_request(
            status_code=404,
            app_hostname="myapp",
            traffic_bytes=256,
        )

        metrics = await collector.get_metrics()

        host_stats = metrics["by_app_hostname"]["myapp"]
        assert host_stats["requests"] == 2
        assert host_stats["errors"] == 1
        assert host_stats["traffic_bytes"] == 1280

    @pytest.mark.asyncio
    async def test_no_by_image_key_when_no_image_requests(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=200)

        metrics = await collector.get_metrics()

        assert "by_image" not in metrics

    @pytest.mark.asyncio
    async def test_no_by_hostname_key_when_no_hostname_requests(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=200)

        metrics = await collector.get_metrics()

        assert "by_app_hostname" not in metrics


@pytest.mark.unit
class TestUpdateMapping:
    """Tests for update_mapping() and get_active_mappings()."""

    @pytest.mark.asyncio
    async def test_stores_hostname_to_port_mapping(
        self, collector: MetricsCollector
    ) -> None:
        await collector.update_mapping("myapp", 32100)

        mappings = await collector.get_active_mappings()

        assert mappings["myapp"] == 32100

    @pytest.mark.asyncio
    async def test_overwrites_existing_mapping(
        self, collector: MetricsCollector
    ) -> None:
        await collector.update_mapping("myapp", 32100)
        await collector.update_mapping("myapp", 32200)

        mappings = await collector.get_active_mappings()

        assert mappings["myapp"] == 32200

    @pytest.mark.asyncio
    async def test_stores_multiple_mappings(
        self, collector: MetricsCollector
    ) -> None:
        await collector.update_mapping("app-a", 32100)
        await collector.update_mapping("app-b", 32101)

        mappings = await collector.get_active_mappings()

        assert mappings["app-a"] == 32100
        assert mappings["app-b"] == 32101

    @pytest.mark.asyncio
    async def test_remove_mapping_deletes_entry(
        self, collector: MetricsCollector
    ) -> None:
        await collector.update_mapping("myapp", 32100)
        await collector.remove_mapping("myapp")

        mappings = await collector.get_active_mappings()

        assert "myapp" not in mappings

    @pytest.mark.asyncio
    async def test_mappings_appear_in_get_metrics(
        self, collector: MetricsCollector
    ) -> None:
        await collector.update_mapping("myapp", 32100)

        metrics = await collector.get_metrics()

        assert metrics["active_mappings"]["myapp"] == 32100

    @pytest.mark.asyncio
    async def test_empty_mappings_not_in_get_metrics(
        self, collector: MetricsCollector
    ) -> None:
        metrics = await collector.get_metrics()

        assert "active_mappings" not in metrics


@pytest.mark.unit
class TestReset:
    """Tests for reset() — clears all lb:metrics:* keys."""

    @pytest.mark.asyncio
    async def test_reset_clears_all_counters(
        self, collector: MetricsCollector
    ) -> None:
        await collector.record_request(status_code=200, latency_ms=100.0, image_id=1)
        await collector.update_mapping("myapp", 32100)

        await collector.reset()

        metrics = await collector.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["avg_latency_ms"] == 0.0
        assert metrics["status_codes"] == {}
        assert "by_image" not in metrics
        assert "active_mappings" not in metrics

    @pytest.mark.asyncio
    async def test_reset_on_empty_state_is_safe(
        self, collector: MetricsCollector
    ) -> None:
        await collector.reset()

        metrics = await collector.get_metrics()

        assert metrics["total_requests"] == 0


@pytest.mark.unit
class TestGetMetricsEmptyState:
    """Tests for get_metrics() when Redis has no data."""

    @pytest.mark.asyncio
    async def test_returns_zeros_when_empty(
        self, collector: MetricsCollector
    ) -> None:
        metrics = await collector.get_metrics()

        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["avg_latency_ms"] == 0.0
        assert metrics["status_codes"] == {}
