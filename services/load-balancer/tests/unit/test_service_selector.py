"""
Unit tests for RoundRobinSelector.
"""
import pytest

from app.services.service_selector import RoundRobinSelector
from app.schemas.service_info import ServiceInfo


@pytest.mark.unit
class TestServiceSelector:
    """Round robin selection tests."""

    def test_select_cycles_per_image(self):
        selector = RoundRobinSelector()
        services = [
            ServiceInfo(
                container_id="a",
                container_ip="10.0.0.1",
                internal_port=80,
                external_port=30000,
                status="passing",
                image_id=1,
                app_hostname="demo",
            ),
            ServiceInfo(
                container_id="b",
                container_ip="10.0.0.2",
                internal_port=80,
                external_port=30001,
                status="passing",
                image_id=1,
                app_hostname="demo",
            ),
        ]

        first = selector.select(1, services)
        second = selector.select(1, services)
        third = selector.select(1, services)

        assert first.container_id == "a"
        assert second.container_id == "b"
        assert third.container_id == "a"  # wraps around

    def test_select_none_when_empty(self):
        selector = RoundRobinSelector()

        assert selector.select(1, []) is None
