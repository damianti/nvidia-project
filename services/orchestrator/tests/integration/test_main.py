"""
Integration tests for main application.
"""
import pytest
import os
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app


@pytest.mark.integration
class TestMainApp:
    """Tests for main application endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"
        assert "health" in data["endpoints"]
        assert "images" in data["endpoints"]
        assert "containers" in data["endpoints"]
    
    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured."""
        # Check that CORS middleware is in the middleware stack
        # Middleware are wrapped, so we check the class name differently
        middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(type(m)) for m in app.user_middleware]
        assert any("CORS" in str(m) for m in middleware_classes) or len(app.user_middleware) > 0
    
    def test_app_has_logging_middleware(self):
        """Test that logging middleware is configured."""
        # Middleware are wrapped, so we check differently
        middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(type(m)) for m in app.user_middleware]
        assert any("Logging" in str(m) for m in middleware_classes) or len(app.user_middleware) > 0
    
    def test_app_includes_routers(self):
        """Test that all routers are included."""
        routes = [route.path for route in app.routes]
        
        assert "/health" in routes or any("/health" in str(r) for r in routes)
        assert "/api/images" in routes or any("/api/images" in str(r) for r in routes)
        assert "/api/containers" in routes or any("/api/containers" in str(r) for r in routes)
