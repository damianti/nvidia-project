"""
Integration tests for containers API endpoints.
"""
import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app
from app.schemas.container import ContainerResponse, ContainerCreate


@pytest.mark.integration
class TestContainersEndpoints:
    """Tests for containers API endpoints."""
    
    @patch('app.api.containers.get_user_id')
    @patch('app.api.containers.get_db')
    @patch('app.api.containers.container_service.create_containers')
    def test_create_containers(self, mock_create, mock_get_db, mock_get_user_id):
        """Test creating containers via API."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_containers = [
            ContainerResponse(
                id=1, container_id="docker-123", container_ip="172.17.0.2",
                name="test-container", internal_port=8080, external_port=32768,
                status="running", cpu_usage="0.0", memory_usage="0m",
                created_at="2024-01-01T00:00:00", image_id=1, user_id=1
            )
        ]
        mock_create.return_value = mock_containers
        
        client = TestClient(app)
        data = {"name": "test-container", "image_id": 1, "count": 1}
        response = client.post("/api/containers/1", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "test-container"
    
    @patch('app.api.containers.get_user_id')
    @patch('app.api.containers.get_db')
    @patch('app.api.containers.container_service.get_all_containers')
    def test_list_containers(self, mock_get_all, mock_get_db, mock_get_user_id):
        """Test listing all containers."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_containers = [
            ContainerResponse(
                id=1, container_id="docker-123", container_ip="172.17.0.2",
                name="container1", internal_port=8080, external_port=32768,
                status="running", cpu_usage="0.0", memory_usage="0m",
                created_at="2024-01-01T00:00:00", image_id=1, user_id=1
            ),
            ContainerResponse(
                id=2, container_id="docker-456", container_ip="172.17.0.3",
                name="container2", internal_port=8080, external_port=32769,
                status="stopped", cpu_usage="0.0", memory_usage="0m",
                created_at="2024-01-01T00:00:00", image_id=1, user_id=1
            ),
        ]
        mock_get_all.return_value = mock_containers
        
        client = TestClient(app)
        response = client.get("/api/containers/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "container1"
    
    @patch('app.api.containers.get_user_id')
    @patch('app.api.containers.get_db')
    @patch('app.api.containers.container_service.start_container')
    def test_start_container(self, mock_start, mock_get_db, mock_get_user_id):
        """Test starting a container."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_container = ContainerResponse(
            id=1, container_id="docker-123", container_ip="172.17.0.2",
            name="test-container", internal_port=8080, external_port=32768,
            status="running", cpu_usage="0.0", memory_usage="0m",
            created_at="2024-01-01T00:00:00", image_id=1, user_id=1
        )
        mock_start.return_value = mock_container
        
        client = TestClient(app)
        response = client.post("/api/containers/1/start")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        mock_start.assert_called_once_with(mock_db, 1, 1)
    
    @patch('app.api.containers.get_user_id')
    @patch('app.api.containers.get_db')
    @patch('app.api.containers.container_service.stop_container')
    def test_stop_container(self, mock_stop, mock_get_db, mock_get_user_id):
        """Test stopping a container."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_container = ContainerResponse(
            id=1, container_id="docker-123", container_ip="172.17.0.2",
            name="test-container", internal_port=8080, external_port=32768,
            status="stopped", cpu_usage="0.0", memory_usage="0m",
            created_at="2024-01-01T00:00:00", image_id=1, user_id=1
        )
        mock_stop.return_value = mock_container
        
        client = TestClient(app)
        response = client.post("/api/containers/1/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        mock_stop.assert_called_once_with(mock_db, 1, 1)
    
    @patch('app.api.containers.get_user_id')
    @patch('app.api.containers.get_db')
    @patch('app.api.containers.container_service.delete_container')
    def test_delete_container(self, mock_delete, mock_get_db, mock_get_user_id):
        """Test deleting a container."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_container = ContainerResponse(
            id=1, container_id="docker-123", container_ip="172.17.0.2",
            name="test-container", internal_port=8080, external_port=32768,
            status="stopped", cpu_usage="0.0", memory_usage="0m",
            created_at="2024-01-01T00:00:00", image_id=1, user_id=1
        )
        mock_delete.return_value = mock_container
        
        client = TestClient(app)
        response = client.delete("/api/containers/1")
        
        assert response.status_code == 200
        mock_delete.assert_called_once_with(mock_db, 1, 1)
