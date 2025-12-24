"""
Integration tests for LoggingMiddleware headers.
"""

from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client_with_middleware() -> TestClient:
    """TestClient with lifespan disabled for quick tests."""

    @asynccontextmanager
    async def dummy_lifespan(_):
        yield

    app.router.lifespan_context = lambda _: dummy_lifespan(app)
    return TestClient(app)


@pytest.mark.integration
class TestLoggingMiddleware:
    """Ensure correlation ID propagation."""

    def test_adds_correlation_id_when_missing(self, client_with_middleware: TestClient):
        response = client_with_middleware.get("/health")

        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"]

    def test_preserves_existing_correlation_id(
        self, client_with_middleware: TestClient
    ):
        correlation = "existing-corr-id"

        response = client_with_middleware.get(
            "/health", headers={"X-Correlation-ID": correlation}
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == correlation
