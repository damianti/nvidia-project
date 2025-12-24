"""
Integration tests for LoggingMiddleware.
"""

from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.mark.integration
class TestLoggingMiddleware:
    """Verifies X-Correlation-ID injection."""

    def test_agrega_correlation_id_si_no_existe(self) -> None:
        @asynccontextmanager
        async def dummy_lifespan(_):
            yield

        app.router.lifespan_context = lambda _: dummy_lifespan(app)

        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"]

    def test_preserva_correlation_id_existente(self) -> None:
        correlation = "test-corr-id"

        @asynccontextmanager
        async def dummy_lifespan(_):
            yield

        app.router.lifespan_context = lambda _: dummy_lifespan(app)

        with TestClient(app) as client:
            response = client.get("/health", headers={"X-Correlation-ID": correlation})

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == correlation

    def test_middleware_registra_error_en_excepcion(self) -> None:
        """Middleware preserves correlation id when endpoint raises."""
        from fastapi import APIRouter, HTTPException

        @asynccontextmanager
        async def dummy_lifespan(_):
            yield

        app.router.lifespan_context = lambda _: dummy_lifespan(app)

        router = APIRouter()

        @router.get("/boom")
        async def boom():
            raise HTTPException(status_code=500, detail="boom")

        app.include_router(router)

        with TestClient(app) as client:
            response = client.get("/boom")

        assert response.status_code == 500
        assert "X-Correlation-ID" in response.headers
