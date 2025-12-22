"""
Integration tests for images API endpoints.
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app
from app.schemas.image import ImageResponse


@pytest.mark.integration
class TestImagesEndpoints:
    """Tests for images API endpoints."""
    
    @patch('app.api.images.get_user_id')
    @patch('app.api.images.get_db')
    @patch('app.api.images.image_service.create_image_from_upload')
    def test_create_image(self, mock_create, mock_get_db, mock_get_user_id):
        """Test creating an image via API."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_image = ImageResponse(
            id=1,
            name="test-app",
            tag="latest",
            app_hostname="test.com",
            container_port=8080,
            min_instances=1,
            max_instances=3,
            cpu_limit="0.5",
            memory_limit="512m",
            status="ready",
            user_id=1,
            created_at="2024-01-01T00:00:00"
        )
        mock_create.return_value = mock_image
        
        client = TestClient(app)
        files = {"file": ("test.zip", b"fake zip content", "application/zip")}
        data = {
            "name": "test-app",
            "tag": "latest",
            "app_hostname": "test.com",
            "container_port": 8080,
            "min_instances": 1,
            "max_instances": 3,
            "cpu_limit": "0.5",
            "memory_limit": "512m",
        }
        
        response = client.post("/api/images/", files=files, data=data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-app"
        assert data["app_hostname"] == "test.com"
    
    @patch('app.api.images.get_user_id')
    @patch('app.api.images.get_db')
    @patch('app.api.images.image_service.get_all_images')
    def test_list_images(self, mock_get_all, mock_get_db, mock_get_user_id):
        """Test listing all images."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_images = [
            ImageResponse(
                id=1, name="app1", tag="latest", app_hostname="app1.com",
                container_port=8080, min_instances=1, max_instances=3,
                cpu_limit="0.5", memory_limit="512m", status="ready",
                user_id=1, created_at="2024-01-01T00:00:00"
            ),
            ImageResponse(
                id=2, name="app2", tag="v1", app_hostname="app2.com",
                container_port=8080, min_instances=1, max_instances=3,
                cpu_limit="0.5", memory_limit="512m", status="ready",
                user_id=1, created_at="2024-01-01T00:00:00"
            ),
        ]
        mock_get_all.return_value = mock_images
        
        client = TestClient(app)
        response = client.get("/api/images/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "app1"
    
    @patch('app.api.images.get_user_id')
    @patch('app.api.images.get_db')
    @patch('app.api.images.image_service.get_image_by_id')
    def test_get_image(self, mock_get_image, mock_get_db, mock_get_user_id):
        """Test getting a specific image."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_image = ImageResponse(
            id=1, name="test-app", tag="latest", app_hostname="test.com",
            container_port=8080, min_instances=1, max_instances=3,
            cpu_limit="0.5", memory_limit="512m", status="ready",
            user_id=1, created_at="2024-01-01T00:00:00"
        )
        mock_get_image.return_value = mock_image
        
        client = TestClient(app)
        response = client.get("/api/images/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "test-app"
    
    @patch('app.api.images.get_user_id')
    @patch('app.api.images.get_db')
    @patch('app.api.images.image_service.get_image_by_id')
    def test_get_image_build_logs(self, mock_get_image, mock_get_db, mock_get_user_id):
        """Test getting build logs for an image."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_image = Mock()
        mock_image.build_logs = "Step 1/5: FROM python:3.11\nStep 2/5: COPY app.py ."
        mock_get_image.return_value = mock_image
        
        client = TestClient(app)
        response = client.get("/api/images/1/build-logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "build_logs" in data
        assert "Step 1/5" in data["build_logs"]
    
    @patch('app.api.images.get_user_id')
    @patch('app.api.images.get_db')
    @patch('app.api.images.image_service.delete_image')
    def test_delete_image(self, mock_delete, mock_get_db, mock_get_user_id):
        """Test deleting an image."""
        mock_get_user_id.return_value = 1
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_delete.return_value = None
        
        client = TestClient(app)
        response = client.delete("/api/images/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        mock_delete.assert_called_once_with(mock_db, 1, 1)
