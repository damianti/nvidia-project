"""
Unit tests for AppHostnameMapping.
"""
import pytest

from app.services.website_mapping import AppHostnameMapping


@pytest.mark.unit
class TestAppHostnameMapping:
    """Hostname mapping tests."""

    def test_add_y_get_image(self) -> None:
        """Adds and retrieves image_id normalizing hostname."""
        mapping = AppHostnameMapping()

        mapping.add("https://Demo.EXAMPLE.com/", 5)

        assert mapping.get_image_id("demo.example.com") == 5
        assert mapping.size() == 1

    def test_add_hostname_vacio_no_agrega(self) -> None:
        """Does not add empty entries."""
        mapping = AppHostnameMapping()

        mapping.add("   ", 1)

        assert mapping.size() == 0

    def test_conflicto_image_id_registra_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """When reassigning same hostname, new image_id overwrites and warns."""
        mapping = AppHostnameMapping()
        mapping.add("app.localhost", 1)

        with caplog.at_level("WARNING", logger="service-discovery"):
            mapping.add("app.localhost", 2)

        assert mapping.get_image_id("app.localhost") == 2
        assert mapping.size() == 1

    def test_remove_image(self) -> None:
        """Removes only when image_id matches."""
        mapping = AppHostnameMapping()
        mapping.add("app.localhost", 1)

        mapping.remove_image("app.localhost", 2)
        assert mapping.size() == 1

        mapping.remove_image("app.localhost", 1)
        assert mapping.size() == 0

    def test_clear(self) -> None:
        """Clears the mapping."""
        mapping = AppHostnameMapping()
        mapping.add("a.com", 1)
        mapping.add("b.com", 2)

        mapping.clear()

        assert mapping.size() == 0
