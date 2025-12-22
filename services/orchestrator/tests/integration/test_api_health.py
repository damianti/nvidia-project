"""
Integration tests for health API endpoints.
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    @patch('app.api.health.get_db')
    @patch('app.api.health.docker')
    def test_health_check_success(self, mock_docker, mock_get_db):
        """Test health check when all services are healthy."""
        # Mock database
        mock_db = Mock()
        mock_db.execute = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock Docker
        mock_docker_client = Mock()
        mock_docker_client.ping = Mock()
        mock_docker.from_env.return_value = mock_docker_client
        
        client = TestClient(app)
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["docker"] == "connected"
    
    @patch('app.api.health.get_db')
    @patch('app.api.health.docker')
    def test_health_check_database_disconnected(self, mock_docker, mock_get_db):
        """Test health check when database is disconnected."""
        # Mock database error
        mock_get_db.return_value = iter([Mock()])
        mock_db = Mock()
        mock_db.execute = Mock(side_effect=Exception("Connection failed"))
        mock_get_db.return_value = iter([mock_db])
        
        # Mock Docker
        mock_docker_client = Mock()
        mock_docker_client.ping = Mock()
        mock_docker.from_env.return_value = mock_docker_client
        
        client = TestClient(app)
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "disconnected" in data["database"]
        assert data["docker"] == "connected"
    
    @patch('app.api.health.get_db')
    @patch('app.api.health.docker')
    def test_health_check_docker_disconnected(self, mock_docker, mock_get_db):
        """Test health check when Docker is disconnected."""
        # Mock database
        mock_db = Mock()
        mock_db.execute = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock Docker error
        mock_docker.from_env.side_effect = Exception("Docker connection failed")
        
        client = TestClient(app)
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "disconnected" in data["docker"]
    
    @patch('app.api.health.get_db')
    @patch('app.api.health.docker')
    def test_health_check_both_disconnected(self, mock_docker, mock_get_db):
        """Test health check when both services are disconnected."""
        # Mock database error
        mock_db = Mock()
        mock_db.execute = Mock(side_effect=Exception("DB failed"))
        mock_get_db.return_value = iter([mock_db])
        
        # Mock Docker error
        mock_docker.from_env.side_effect = Exception("Docker failed")
        
        client = TestClient(app)
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "disconnected" in data["database"]
        assert "disconnected" in data["docker"]
    
    @patch('app.api.health.docker_diagnostics')
    def test_docker_diagnostics_success(self, mock_diagnostics_module):
        """Test docker diagnostics endpoint."""
        mock_diagnostics_module.check_current_user = Mock(return_value={"user": "test"})
        mock_diagnostics_module.check_docker_socket = Mock(return_value={"socket": "ok"})
        mock_diagnostics_module.check_docker_env = Mock(return_value={"env": "ok"})
        mock_diagnostics_module.test_docker_connection_methods = Mock(return_value={"connection": "ok"})
        
        client = TestClient(app)
        response = client.get("/health/docker-diagnostics")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_info" in data
        assert "socket_info" in data
        assert "environment" in data
        assert "connection_tests" in data
    
    @patch('app.api.health.docker_diagnostics')
    def test_docker_diagnostics_error(self, mock_diagnostics_module):
        """Test docker diagnostics endpoint when it fails."""
        # Make import fail
        with patch('app.api.health.docker_diagnostics', side_effect=ImportError("Module not found")):
            client = TestClient(app)
            response = client.get("/health/docker-diagnostics")
            
            assert response.status_code == 500
            assert "Error ejecutando diagnósticos" in response.json()["detail"]
