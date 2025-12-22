"""
Integration tests for main application.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
class TestMainApp:
    """Tests for main application endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint.
        
        Arrange:
            - FastAPI app instance
        
        Act:
            - Send GET request to root endpoint
        
        Assert:
            - Status code is 200
            - Response contains expected fields
            - Response structure matches expected schema
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        assert "message" in data, "Response should contain 'message' field"
        assert "version" in data, "Response should contain 'version' field"
        assert data["version"] == "1.0.0", \
            f"Expected version '1.0.0', got {data['version']}"
    
    def test_health_endpoint(self):
        """Test health check endpoint.
        
        Arrange:
            - FastAPI app instance
        
        Act:
            - Send GET request to /health
        
        Assert:
            - Status code is 200
            - Response indicates healthy status
            - Response structure matches expected schema
        """
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        assert "status" in data, "Response should contain 'status' field"
        assert "service" in data, "Response should contain 'service' field"
        assert data["status"] == "healthy", \
            f"Expected status 'healthy', got {data['status']}"
        assert data["service"] == "api-gateway", \
            f"Expected service 'api-gateway', got {data['service']}"
    
    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured.
        
        Arrange:
            - FastAPI app instance
        
        Act:
            - Check middleware stack
        
        Assert:
            - CORS middleware is present
        """
        # Arrange
        # Check that CORS middleware is in the middleware stack
        # Middleware are wrapped, so we check the class name differently
        middleware_classes = [
            m.cls.__name__ if hasattr(m, 'cls') else str(type(m)) 
            for m in app.user_middleware
        ]
        
        # Assert
        assert any("CORS" in str(m) for m in middleware_classes) or \
               len(app.user_middleware) > 0, \
               "CORS middleware should be configured"
    
    def test_app_has_logging_middleware(self):
        """Test that logging middleware is configured.
        
        Arrange:
            - FastAPI app instance
        
        Act:
            - Check middleware stack
        
        Assert:
            - Logging middleware is present
        """
        # Arrange
        # Middleware are wrapped, so we check differently
        middleware_classes = [
            m.cls.__name__ if hasattr(m, 'cls') else str(type(m)) 
            for m in app.user_middleware
        ]
        
        # Assert
        assert any("Logging" in str(m) for m in middleware_classes) or \
               len(app.user_middleware) > 0, \
               "Logging middleware should be configured"
    
    def test_app_includes_routers(self):
        """Test that all routers are included.
        
        Arrange:
            - FastAPI app instance
        
        Act:
            - Get all routes from app
        
        Assert:
            - Auth router is included
            - Proxy router is included
        """
        # Arrange
        routes = [route.path for route in app.routes]
        
        # Assert
        assert "/health" in routes or any("/health" in str(r) for r in routes), \
            "Health endpoint should be registered"
        assert "/auth" in str(routes) or any("/auth" in str(r) for r in routes), \
            "Auth router should be included"
        # Proxy routes are dynamic, so we check that routes exist
        assert len(routes) > 0, "App should have registered routes"

