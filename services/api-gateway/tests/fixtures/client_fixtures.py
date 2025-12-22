"""
Fixtures for HTTP client and test client setup.
"""
import pytest
from unittest.mock import AsyncMock
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Fixture providing a mocked httpx.AsyncClient.
    
    Returns:
        AsyncMock configured as httpx.AsyncClient.
    """
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def test_app() -> FastAPI:
    """Fixture providing the FastAPI application instance.
    
    Returns:
        FastAPI app instance configured for testing.
    """
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Fixture providing a FastAPI TestClient.
    
    Args:
        test_app: FastAPI application fixture.
    
    Returns:
        TestClient instance for making HTTP requests to the app.
    """
    return TestClient(test_app)

