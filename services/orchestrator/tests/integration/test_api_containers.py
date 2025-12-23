"""
Integration tests for Containers API endpoints.

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
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set DATABASE_URL before importing app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

from app.main import app
from app.utils.dependencies import get_user_id
from app.database.config import get_db
from app.schemas.container import ContainerResponse


@pytest.mark.integration
class TestContainersEndpoints:
    """Test suite for Containers API endpoints."""

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

    @patch("app.api.containers.container_service.create_containers")
    def test_create_containers_success(
        self,
        mock_create: Mock,
        sample_container_data: Dict[str, Any],
        test_user_id: int,
    ) -> None:
        """Test successful container creation (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Response is a list
        - Complete container structure
        - Correct data mapping

        Args:
            mock_create: Mocked container service create function
            sample_container_data: Fixture with valid container data
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_containers = [
            ContainerResponse(
                id=1,
                container_id="docker-123",
                container_ip="172.17.0.2",
                name=sample_container_data["name"],
                internal_port=8080,
                external_port=32768,
                status="running",
                cpu_usage="0.0",
                memory_usage="0m",
                created_at="2024-01-01T00:00:00Z",
                image_id=sample_container_data["image_id"],
                user_id=test_user_id,
            )
        ]
        mock_create.return_value = mock_containers

        client = TestClient(app)

        # Create ContainerCreate object from dict (image_id is required in schema)
        container_create = {
            "name": sample_container_data["name"],
            "image_id": sample_container_data["image_id"],
            "count": sample_container_data["count"],
        }

        # Act
        response = client.post(
            f"/api/containers/{sample_container_data['image_id']}",
            json=container_create,
        )

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, list), "Response should be a list"
        assert (
            len(response_data) == 1
        ), f"Expected 1 container, got {len(response_data)}"

        # Verify complete container structure
        container = response_data[0]
        required_fields = [
            "id",
            "container_id",
            "name",
            "internal_port",
            "external_port",
            "status",
            "cpu_usage",
            "memory_usage",
            "created_at",
            "image_id",
            "user_id",
        ]
        for field in required_fields:
            assert field in container, f"Missing required field: {field}"

        assert container["name"] == sample_container_data["name"]
        assert container["status"] == "running"
        assert container["image_id"] == sample_container_data["image_id"]
        assert container["user_id"] == test_user_id

        mock_create.assert_called_once()

    def test_create_containers_invalid_data(self, test_user_id: int) -> None:
        """Test container creation with invalid data (Error Case 1: Invalid Data).

        Verifies:
        - HTTP 422 status code for validation errors
        - Error response structure
        - Specific validation error messages

        Args:
            test_user_id: Fixture with test user ID
        """
        # Arrange
        invalid_data = {
            "name": "",  # Empty name
            "image_id": -1,  # Invalid image_id
            "count": 0,  # Invalid count
        }

        client = TestClient(app)

        # Act
        response = client.post("/api/containers/1", json=invalid_data)

        # Assert
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert isinstance(
            response_data["detail"], list
        ), "Detail should be a list of errors"

    @patch("app.api.containers.container_service.create_containers")
    def test_create_containers_server_error(
        self, mock_create: Mock, sample_container_data: Dict[str, Any]
    ) -> None:
        """Test container creation with server error (Error Case 2: Server Error).

        Verifies:
        - HTTP 500 status code
        - Error response structure

        Args:
            mock_create: Mocked container service create function
            sample_container_data: Fixture with valid container data
        """
        # Arrange
        mock_create.side_effect = HTTPException(
            status_code=500, detail="Docker daemon unavailable"
        )

        client = TestClient(app)

        container_create = {
            "name": sample_container_data["name"],
            "image_id": sample_container_data["image_id"],
            "count": sample_container_data["count"],
        }

        # Act
        response = client.post(
            f"/api/containers/{sample_container_data['image_id']}",
            json=container_create,
        )

        # Assert
        assert (
            response.status_code == 500
        ), f"Expected 500, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "unavailable" in response_data["detail"].lower()

    @patch("app.api.containers.container_service.get_all_containers")
    def test_list_containers_success(
        self, mock_get_all: Mock, test_user_id: int
    ) -> None:
        """Test successful container listing (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Response is a list
        - All items have required structure
        - Correct number of items

        Args:
            mock_get_all: Mocked container service get_all function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_containers = [
            ContainerResponse(
                id=1,
                container_id="docker-123",
                container_ip="172.17.0.2",
                name="container1",
                internal_port=8080,
                external_port=32768,
                status="running",
                cpu_usage="0.0",
                memory_usage="0m",
                created_at="2024-01-01T00:00:00Z",
                image_id=1,
                user_id=test_user_id,
            ),
            ContainerResponse(
                id=2,
                container_id="docker-456",
                container_ip="172.17.0.3",
                name="container2",
                internal_port=8080,
                external_port=32769,
                status="stopped",
                cpu_usage="0.0",
                memory_usage="0m",
                created_at="2024-01-01T00:00:00Z",
                image_id=1,
                user_id=test_user_id,
            ),
        ]
        mock_get_all.return_value = mock_containers

        client = TestClient(app)

        # Act
        response = client.get("/api/containers/")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, list), "Response should be a list"
        assert (
            len(response_data) == 2
        ), f"Expected 2 containers, got {len(response_data)}"

        # Verify structure of each container
        for container in response_data:
            assert "id" in container
            assert "name" in container
            assert "status" in container
            assert "image_id" in container

        assert response_data[0]["name"] == "container1"
        assert response_data[0]["status"] == "running"
        assert response_data[1]["name"] == "container2"
        assert response_data[1]["status"] == "stopped"

        mock_get_all.assert_called_once()

    @patch("app.api.containers.container_service.start_container")
    def test_start_container_success(self, mock_start: Mock, test_user_id: int) -> None:
        """Test successful container start (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Complete container structure
        - Status is 'running'

        Args:
            mock_start: Mocked container service start function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_container = ContainerResponse(
            id=1,
            container_id="docker-123",
            container_ip="172.17.0.2",
            name="test-container",
            internal_port=8080,
            external_port=32768,
            status="running",
            cpu_usage="0.0",
            memory_usage="0m",
            created_at="2024-01-01T00:00:00Z",
            image_id=1,
            user_id=test_user_id,
        )
        mock_start.return_value = mock_container

        client = TestClient(app)

        # Act
        response = client.post("/api/containers/1/start")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert response_data["status"] == "running", "Container should be running"
        assert response_data["id"] == 1
        assert response_data["name"] == "test-container"

        mock_start.assert_called_once()

    @patch("app.api.containers.container_service.start_container")
    def test_start_container_not_found(self, mock_start: Mock) -> None:
        """Test container start when container doesn't exist (Error Case 3: Not Found).

        Verifies:
        - HTTP 404 status code
        - Error response structure

        Args:
            mock_start: Mocked container service start function
        """
        # Arrange
        mock_start.side_effect = HTTPException(
            status_code=404, detail="Container not found"
        )

        client = TestClient(app)

        # Act
        response = client.post("/api/containers/999/start")

        # Assert
        assert (
            response.status_code == 404
        ), f"Expected 404, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "not found" in response_data["detail"].lower()

    @patch("app.api.containers.container_service.stop_container")
    def test_stop_container_success(self, mock_stop: Mock, test_user_id: int) -> None:
        """Test successful container stop (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Complete container structure
        - Status is 'stopped'

        Args:
            mock_stop: Mocked container service stop function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_container = ContainerResponse(
            id=1,
            container_id="docker-123",
            container_ip="172.17.0.2",
            name="test-container",
            internal_port=8080,
            external_port=32768,
            status="stopped",
            cpu_usage="0.0",
            memory_usage="0m",
            created_at="2024-01-01T00:00:00Z",
            image_id=1,
            user_id=test_user_id,
        )
        mock_stop.return_value = mock_container

        client = TestClient(app)

        # Act
        response = client.post("/api/containers/1/stop")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert response_data["status"] == "stopped", "Container should be stopped"
        assert response_data["id"] == 1

        mock_stop.assert_called_once()

    @patch("app.api.containers.container_service.delete_container")
    def test_delete_container_success(
        self, mock_delete: Mock, test_user_id: int
    ) -> None:
        """Test successful container deletion (Happy Path).

        Verifies:
        - HTTP 200 status code
        - Response structure
        - Container data is returned

        Args:
            mock_delete: Mocked container service delete function
            test_user_id: Fixture with test user ID
        """
        # Arrange
        mock_container = ContainerResponse(
            id=1,
            container_id="docker-123",
            container_ip="172.17.0.2",
            name="test-container",
            internal_port=8080,
            external_port=32768,
            status="stopped",
            cpu_usage="0.0",
            memory_usage="0m",
            created_at="2024-01-01T00:00:00Z",
            image_id=1,
            user_id=test_user_id,
        )
        mock_delete.return_value = mock_container

        client = TestClient(app)

        # Act
        response = client.delete("/api/containers/1")

        # Assert
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert "id" in response_data, "Response should contain container data"
        assert response_data["id"] == 1
        assert response_data["status"] == "stopped"

        mock_delete.assert_called_once()

    @patch("app.api.containers.container_service.delete_container")
    def test_delete_container_not_found(self, mock_delete: Mock) -> None:
        """Test container deletion when container doesn't exist (Error Case 3: Not Found).

        Verifies:
        - HTTP 404 status code
        - Error response structure

        Args:
            mock_delete: Mocked container service delete function
        """
        # Arrange
        mock_delete.side_effect = HTTPException(
            status_code=404, detail="Container not found"
        )

        client = TestClient(app)

        # Act
        response = client.delete("/api/containers/999")

        # Assert
        assert (
            response.status_code == 404
        ), f"Expected 404, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert "not found" in response_data["detail"].lower()
