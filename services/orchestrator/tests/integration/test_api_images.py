"""
Integration tests for Images API endpoints.

This module implements comprehensive integration tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Fixtures for test data
- Happy path and error scenarios
- Complete response structure validation
- Full type hints and descriptive docstrings
"""
import pytest
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')

from app.main import app
from app.utils.dependencies import get_user_id
from app.database.config import get_db
from app.schemas.image import ImageResponse


@pytest.mark.integration
class TestImagesEndpoints:
    """Test suite for Images API endpoints."""
    
    def setup_method(self) -> None:
        """Setup method that runs before each test.
        
        Configures dependency overrides for database and user authentication.
        """
        # Arrange: Override dependencies
        self.mock_db = Mock()
        self.mock_db.execute = Mock(return_value=Mock())
        app.dependency_overrides[get_user_id] = lambda: 1
        app.dependency_overrides[get_db] = lambda: iter([self.mock_db])
    
    def teardown_method(self) -> None:
        """Teardown method that runs after each test.
        
        Clears all dependency overrides to prevent test interference.
        """
        app.dependency_overrides.clear()
    
    @patch('app.api.images.image_service.create_image_from_upload')
    def test_create_image_success(
        self,
        mock_create: AsyncMock,
        sample_image_data: Dict[str, Any],
        sample_image_file: tuple,
        test_user_id: int
    ) -> None:
        """Test successful image creation (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Complete response structure
        - All required fields are present
        - Correct data mapping
        
        Args:
            mock_create: Mocked image service create function
            sample_image_data: Fixture with valid image data
            sample_image_file: Fixture with test file
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_image = ImageResponse(
            id=1,
            name=sample_image_data["name"],
            tag=sample_image_data["tag"],
            app_hostname=sample_image_data["app_hostname"],
            container_port=sample_image_data["container_port"],
            min_instances=sample_image_data["min_instances"],
            max_instances=sample_image_data["max_instances"],
            cpu_limit=sample_image_data["cpu_limit"],
            memory_limit=sample_image_data["memory_limit"],
            status="ready",
            user_id=test_user_id,
            created_at="2024-01-01T00:00:00Z"
        )
        mock_create.return_value = mock_image
        
        client = TestClient(app)
        files = {"file": sample_image_file}
        
        # Act
        response = client.post("/api/images/", files=files, data=sample_image_data)
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        
        # Verify complete response structure
        required_fields = [
            "id", "name", "tag", "app_hostname", "container_port",
            "min_instances", "max_instances", "cpu_limit", "memory_limit",
            "status", "user_id", "created_at"
        ]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
        
        # Verify data correctness
        assert response_data["id"] == 1
        assert response_data["name"] == sample_image_data["name"]
        assert response_data["tag"] == sample_image_data["tag"]
        assert response_data["app_hostname"] == sample_image_data["app_hostname"]
        assert response_data["container_port"] == sample_image_data["container_port"]
        assert response_data["status"] == "ready"
        assert response_data["user_id"] == test_user_id
        
        # Verify service was called
        mock_create.assert_called_once()
    
    def test_create_image_invalid_data(
        self,
        invalid_image_data: Dict[str, Any],
        sample_image_file: tuple
    ) -> None:
        """Test image creation with invalid data (Error Case 1: Invalid Data).
        
        Verifies:
        - HTTP 422 status code for validation errors
        - Error response structure
        - Specific validation error messages
        
        Args:
            invalid_image_data: Fixture with invalid image data
            sample_image_file: Fixture with test file
        """
        # Arrange
        client = TestClient(app)
        files = {"file": sample_image_file}
        
        # Act
        response = client.post("/api/images/", files=files, data=invalid_image_data)
        
        # Assert
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert isinstance(response_data["detail"], list), "Detail should be a list of errors"
    
    @patch('app.api.images.image_service.create_image_from_upload')
    def test_create_image_server_error(
        self,
        mock_create: AsyncMock,
        sample_image_data: Dict[str, Any],
        sample_image_file: tuple
    ) -> None:
        """Test image creation with server error (Error Case 2: Server Error).
        
        Verifies:
        - HTTP 500 status code
        - Error response structure
        - Error message presence
        
        Args:
            mock_create: Mocked image service create function
            sample_image_data: Fixture with valid image data
            sample_image_file: Fixture with test file
        """
        # Arrange
        from fastapi import HTTPException
        mock_create.side_effect = HTTPException(
            status_code=500,
            detail="Database connection failed"
        )
        
        client = TestClient(app)
        files = {"file": sample_image_file}
        
        # Act
        response = client.post("/api/images/", files=files, data=sample_image_data)
        
        # Assert
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "connection failed" in response_data["detail"].lower()
    
    @patch('app.api.images.image_service.get_all_images')
    def test_list_images_success(
        self,
        mock_get_all: Mock,
        test_user_id: int
    ) -> None:
        """Test successful image listing (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Response is a list
        - All items have required structure
        - Correct number of items
        
        Args:
            mock_get_all: Mocked image service get_all function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_images = [
            ImageResponse(
                id=1, name="app1", tag="latest", app_hostname="app1.com",
                container_port=8080, min_instances=1, max_instances=3,
                cpu_limit="0.5", memory_limit="512m", status="ready",
                user_id=test_user_id, created_at="2024-01-01T00:00:00Z"
            ),
            ImageResponse(
                id=2, name="app2", tag="v1", app_hostname="app2.com",
                container_port=8080, min_instances=1, max_instances=3,
                cpu_limit="0.5", memory_limit="512m", status="ready",
                user_id=test_user_id, created_at="2024-01-01T00:00:00Z"
            ),
        ]
        mock_get_all.return_value = mock_images
        
        client = TestClient(app)
        
        # Act
        response = client.get("/api/images/")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert isinstance(response_data, list), "Response should be a list"
        assert len(response_data) == 2, f"Expected 2 images, got {len(response_data)}"
        
        # Verify structure of each item
        for item in response_data:
            assert "id" in item
            assert "name" in item
            assert "tag" in item
            assert "app_hostname" in item
            assert "status" in item
        
        assert response_data[0]["name"] == "app1"
        assert response_data[1]["name"] == "app2"
        
        mock_get_all.assert_called_once()
    
    @patch('app.api.images.image_service.get_image_by_id')
    def test_get_image_success(
        self,
        mock_get_image: Mock,
        test_user_id: int
    ) -> None:
        """Test successful image retrieval (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Complete response structure
        - Correct image data
        
        Args:
            mock_get_image: Mocked image service get_by_id function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_image = ImageResponse(
            id=1, name="test-app", tag="latest", app_hostname="test.com",
            container_port=8080, min_instances=1, max_instances=3,
            cpu_limit="0.5", memory_limit="512m", status="ready",
            user_id=test_user_id, created_at="2024-01-01T00:00:00Z"
        )
        mock_get_image.return_value = mock_image
        
        client = TestClient(app)
        
        # Act
        response = client.get("/api/images/1")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        
        # Verify complete structure
        assert response_data["id"] == 1
        assert response_data["name"] == "test-app"
        assert response_data["tag"] == "latest"
        assert response_data["app_hostname"] == "test.com"
        assert response_data["status"] == "ready"
        assert response_data["user_id"] == test_user_id
        
        mock_get_image.assert_called_once()
    
    @patch('app.api.images.image_service.get_image_by_id')
    def test_get_image_not_found(
        self,
        mock_get_image: Mock
    ) -> None:
        """Test image retrieval when image doesn't exist (Error Case 3: Not Found).
        
        Verifies:
        - HTTP 404 status code
        - Error response structure
        - Appropriate error message
        
        Args:
            mock_get_image: Mocked image service get_by_id function
        """
        # Arrange
        from fastapi import HTTPException
        mock_get_image.side_effect = HTTPException(
            status_code=404,
            detail="Image not found"
        )
        
        client = TestClient(app)
        
        # Act
        response = client.get("/api/images/999")
        
        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "not found" in response_data["detail"].lower()
    
    @patch('app.api.images.image_service.get_image_by_id')
    def test_get_image_build_logs_success(
        self,
        mock_get_image: Mock
    ) -> None:
        """Test successful build logs retrieval (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Response contains build_logs field
        - Build logs content is present
        
        Args:
            mock_get_image: Mocked image service get_by_id function
        """
        # Arrange
        mock_image = Mock()
        mock_image.build_logs = "Step 1/5: FROM python:3.11\nStep 2/5: COPY app.py ."
        mock_get_image.return_value = mock_image
        
        client = TestClient(app)
        
        # Act
        response = client.get("/api/images/1/build-logs")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "build_logs" in response_data, "Response should contain 'build_logs' field"
        assert isinstance(response_data["build_logs"], str), "build_logs should be a string"
        assert "Step 1/5" in response_data["build_logs"]
        assert "FROM python:3.11" in response_data["build_logs"]
    
    @patch('app.api.images.image_service.delete_image')
    def test_delete_image_success(
        self,
        mock_delete: Mock
    ) -> None:
        """Test successful image deletion (Happy Path).
        
        Verifies:
        - HTTP 200 status code
        - Success message structure
        - Correct message content
        
        Args:
            mock_delete: Mocked image service delete function
        """
        # Arrange
        mock_delete.return_value = None
        
        client = TestClient(app)
        
        # Act
        response = client.delete("/api/images/1")
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "message" in response_data, "Response should contain 'message' field"
        assert isinstance(response_data["message"], str), "message should be a string"
        assert "deleted successfully" in response_data["message"].lower()
        assert "1" in response_data["message"]
        
        mock_delete.assert_called_once()
    
    @patch('app.api.images.image_service.delete_image')
    def test_delete_image_not_found(
        self,
        mock_delete: Mock
    ) -> None:
        """Test image deletion when image doesn't exist (Error Case 3: Not Found).
        
        Verifies:
        - HTTP 404 status code
        - Error response structure
        
        Args:
            mock_delete: Mocked image service delete function
        """
        # Arrange
        from fastapi import HTTPException
        mock_delete.side_effect = HTTPException(
            status_code=404,
            detail="Image not found"
        )
        
        client = TestClient(app)
        
        # Act
        response = client.delete("/api/images/999")
        
        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"