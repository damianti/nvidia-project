"""
Unit tests for container service.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.application.services.container_service import (
    create_containers,
    start_container,
    stop_container,
    delete_container,
)
from app.schemas.container import ContainerCreate
from app.database.models import Container, ContainerStatus, Image


class TestCreateContainers:
    """Tests for create_containers function."""

    @patch("app.application.services.container_service.KafkaProducerSingleton")
    @patch("app.application.services.container_service.docker_service")
    @patch("app.application.services.container_service.containers_repository")
    @patch("app.application.services.container_service.images_repository")
    def test_create_containers_success(
        self, mock_images_repo, mock_containers_repo, mock_docker, mock_kafka
    ):
        """Test successful container creation."""
        # Setup mocks
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_image.app_hostname = "example.com"
        mock_image.max_instances = 10
        mock_image.name = "nginx"
        mock_image.tag = "latest"
        mock_image.container_port = 8080
        mock_images_repo.get_by_id.return_value = mock_image

        mock_containers_repo.get_containers_by_image_id.return_value = []

        mock_docker_container = Mock()
        mock_docker_container.id = "docker-container-id-123"
        mock_docker_container.name = "test-container"
        mock_docker.run_container.return_value = (
            mock_docker_container,
            8080,
            "172.17.0.2",
        )

        mock_kafka_instance = Mock()
        mock_kafka.instance.return_value = mock_kafka_instance
        mock_kafka_instance.produce_json = Mock()

        db = Mock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()

        # Test
        container_data = ContainerCreate(name="test-container", count=2, image_id=1)
        result = create_containers(
            db, image_id=1, user_id=1, container_data=container_data
        )

        # Assertions
        assert len(result) == 2
        mock_images_repo.get_by_id.assert_called_once_with(db, 1, 1)
        assert mock_docker.run_container.call_count == 2
        assert mock_containers_repo.create.call_count == 2
        db.commit.assert_called_once()
        assert mock_kafka_instance.produce_json.call_count == 2

    @patch("app.application.services.container_service.images_repository")
    def test_create_containers_image_not_found(self, mock_images_repo):
        """Test container creation with non-existent image."""
        mock_images_repo.get_by_id.return_value = None

        db = Mock(spec=Session)
        container_data = ContainerCreate(name="test-container", count=1, image_id=999)

        with pytest.raises(HTTPException) as exc_info:
            create_containers(
                db, image_id=999, user_id=1, container_data=container_data
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @patch("app.application.services.container_service.images_repository")
    def test_create_containers_invalid_count_zero(self, mock_images_repo):
        """Test container creation with zero count."""
        with pytest.raises(ValidationError):
            ContainerCreate(name="test-container", count=0, image_id=1)

    @patch("app.application.services.container_service.images_repository")
    def test_create_containers_invalid_count_too_many(self, mock_images_repo):
        """Test container creation with count exceeding limit."""
        with pytest.raises(ValidationError):
            ContainerCreate(name="test-container", count=11, image_id=1)


@pytest.mark.unit
class TestStartContainer:
    """Tests for start_container function."""

    @patch("app.application.services.container_service.KafkaProducerSingleton")
    @patch("app.application.services.container_service.images_repository")
    @patch("app.application.services.container_service.docker_service")
    @patch("app.application.services.container_service.containers_repository")
    def test_start_container_success(
        self, mock_containers_repo, mock_docker, mock_images_repo, mock_kafka
    ):
        """Test successful container start."""
        # Setup mocks
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.container_id = "docker-id-123"
        mock_container.status = ContainerStatus.STOPPED
        mock_container.image_id = 1
        mock_container.internal_port = 8080
        mock_containers_repo.get_by_id_and_user.return_value = mock_container

        mock_image = Mock(spec=Image)
        mock_image.app_hostname = "example.com"
        mock_images_repo.get_by_id.return_value = mock_image

        mock_docker_container = Mock()
        mock_docker_container.id = "docker-id-123"
        mock_docker_container.name = "test-container"
        mock_docker.start_container.return_value = (
            mock_docker_container,
            8080,
            "172.17.0.2",
        )

        mock_kafka_instance = Mock()
        mock_kafka.instance.return_value = mock_kafka_instance

        db = Mock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()

        # Test
        result = start_container(db, user_id=1, container_id=1)

        # Assertions
        assert result.status == ContainerStatus.RUNNING
        mock_docker.start_container.assert_called_once_with(
            "docker-id-123", internal_port=8080
        )
        db.commit.assert_called_once()

    @patch("app.application.services.container_service.containers_repository")
    def test_start_container_not_found(self, mock_containers_repo):
        """Test starting non-existent container."""
        mock_containers_repo.get_by_id_and_user.return_value = None

        db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            start_container(db, user_id=1, container_id=999)

        assert exc_info.value.status_code == 404

    @patch("app.application.services.container_service.containers_repository")
    def test_start_container_already_running(self, mock_containers_repo):
        """Test starting container that is already running."""
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.status = ContainerStatus.RUNNING
        mock_containers_repo.get_by_id_and_user.return_value = mock_container

        db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            start_container(db, user_id=1, container_id=1)

        assert exc_info.value.status_code == 400
        assert "already running" in str(exc_info.value.detail).lower()


@pytest.mark.unit
class TestStopContainer:
    """Tests for stop_container function."""

    @patch("app.application.services.container_service.KafkaProducerSingleton")
    @patch("app.application.services.container_service.images_repository")
    @patch("app.application.services.container_service.docker_service")
    @patch("app.application.services.container_service.containers_repository")
    def test_stop_container_success(
        self, mock_containers_repo, mock_docker, mock_images_repo, mock_kafka
    ):
        """Test successful container stop."""
        # Setup mocks
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.container_id = "docker-id-123"
        mock_container.status = ContainerStatus.RUNNING
        mock_container.image_id = 1
        mock_containers_repo.get_by_id_and_user.return_value = mock_container

        mock_image = Mock(spec=Image)
        mock_image.app_hostname = "example.com"
        mock_images_repo.get_by_id.return_value = mock_image

        mock_kafka_instance = Mock()
        mock_kafka.instance.return_value = mock_kafka_instance

        db = Mock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()

        # Test
        result = stop_container(db, user_id=1, container_id=1)

        # Assertions
        assert result.status == ContainerStatus.STOPPED
        mock_docker.stop_container.assert_called_once_with("docker-id-123")
        db.commit.assert_called_once()

    @patch("app.application.services.container_service.containers_repository")
    def test_stop_container_not_found(self, mock_containers_repo):
        """Test stopping non-existent container."""
        mock_containers_repo.get_by_id_and_user.return_value = None

        db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            stop_container(db, user_id=1, container_id=999)

        assert exc_info.value.status_code == 404

    @patch("app.application.services.container_service.containers_repository")
    def test_stop_container_already_stopped(self, mock_containers_repo):
        """Test stopping container that is already stopped."""
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.status = ContainerStatus.STOPPED
        mock_containers_repo.get_by_id_and_user.return_value = mock_container

        db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            stop_container(db, user_id=1, container_id=1)

        assert exc_info.value.status_code == 400
        assert "already stopped" in str(exc_info.value.detail).lower()


@pytest.mark.unit
class TestDeleteContainer:
    """Tests for delete_container function."""

    @patch("app.application.services.container_service.KafkaProducerSingleton")
    @patch("app.application.services.container_service.images_repository")
    @patch("app.application.services.container_service.docker_service")
    @patch("app.application.services.container_service.containers_repository")
    def test_delete_container_success(
        self, mock_containers_repo, mock_docker, mock_images_repo, mock_kafka
    ):
        """Test successful container deletion."""
        # Setup mocks
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.container_id = "docker-id-123"
        mock_container.image_id = 1
        mock_container.user_id = 1
        mock_container.name = "test-container"
        mock_container.container_ip = "172.17.0.2"
        mock_container.internal_port = 80
        mock_container.external_port = 8080
        mock_containers_repo.get_by_id_and_user.return_value = mock_container

        mock_image = Mock(spec=Image)
        mock_image.app_hostname = "example.com"
        mock_images_repo.get_by_id.return_value = mock_image

        mock_kafka_instance = Mock()
        mock_kafka.instance.return_value = mock_kafka_instance

        db = Mock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()

        # Test
        result = delete_container(db, user_id=1, container_id=1)

        # Assertions
        assert "deleted" in result.get("message", "").lower()
        mock_docker.delete_container.assert_called_once_with("docker-id-123")
        db.delete.assert_called_once_with(mock_container)
        db.commit.assert_called_once()

    @patch("app.application.services.container_service.containers_repository")
    def test_delete_container_not_found(self, mock_containers_repo):
        """Test deleting non-existent container."""
        mock_containers_repo.get_by_id_and_user.return_value = None

        db = Mock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            delete_container(db, user_id=1, container_id=999)

        assert exc_info.value.status_code == 404
