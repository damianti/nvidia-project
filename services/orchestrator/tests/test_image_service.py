"""
Unit tests for image service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Mock psycopg2 before importing models
import sys
sys.modules['psycopg2'] = MagicMock()
sys.modules['confluent_kafka'] = MagicMock()

from app.application.services.image_service import create_image_from_upload, get_image_by_id, delete_image
from app.schemas.image import ImageCreate
from app.database.models import Image, ContainerStatus


class TestCreateImageFromUpload:
    """Tests for create_image_from_upload function."""

    @patch("app.application.services.image_service.docker_service.build_image_from_context")
    @patch("app.application.services.image_service.prepare_context")
    @patch("app.application.services.image_service.images_repository")
    def test_create_image_from_upload_success(self, mock_repo, mock_prepare, mock_build):
        mock_repo.get_by_app_hostname.return_value = None

        def mock_create(db_session, image_obj):
            image_obj.id = 1
            return image_obj

        mock_repo.create.side_effect = mock_create
        mock_prepare.return_value = ("/tmp/root", "/tmp/root/context")

        db = Mock(spec=Session)
        db.flush = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        data = ImageCreate(
            name="myapp",
            tag="latest",
            app_hostname="example.com",
            container_port=8080,
            min_instances=1,
            max_instances=3,
            cpu_limit="0.5",
            memory_limit="512m",
            user_id=1,
        )
        file = Mock()
        file.filename = "app.zip"

        result = create_image_from_upload(db=db, data=data, file=file)

        assert result.id == 1
        mock_prepare.assert_called_once()
        mock_build.assert_called_once_with("/tmp/root/context", "nvidia-app-u1-i1", "latest")
        db.commit.assert_called_once()

    @patch("app.application.services.image_service.docker_service.build_image_from_context")
    @patch("app.application.services.image_service.prepare_context")
    @patch("app.application.services.image_service.images_repository")
    def test_create_image_from_upload_duplicate_app_hostname(self, mock_repo, mock_prepare, mock_build):
        mock_repo.get_by_app_hostname.return_value = Mock(spec=Image)

        db = Mock(spec=Session)
        data = ImageCreate(
            name="myapp",
            tag="latest",
            app_hostname="example.com",
            container_port=8080,
            min_instances=1,
            max_instances=3,
            cpu_limit="0.5",
            memory_limit="512m",
            user_id=1,
        )
        file = Mock()
        file.filename = "app.zip"

        with pytest.raises(HTTPException) as exc_info:
            create_image_from_upload(db=db, data=data, file=file)

        assert exc_info.value.status_code == 400
        mock_prepare.assert_not_called()
        mock_build.assert_not_called()


class TestGetImageById:
    """Tests for get_image_by_id function."""
    
    @patch('app.application.services.image_service.images_repository')
    def test_get_image_by_id_success(self, mock_repo):
        """Test successful image retrieval."""
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_repo.get_by_id.return_value = mock_image
        
        db = Mock(spec=Session)
        result = get_image_by_id(db, image_id=1, user_id=1)
        
        assert result == mock_image
        mock_repo.get_by_id.assert_called_once_with(db, 1, 1)
    
    @patch('app.application.services.image_service.images_repository')
    def test_get_image_by_id_not_found(self, mock_repo):
        """Test image retrieval when image doesn't exist."""
        mock_repo.get_by_id.return_value = None
        
        db = Mock(spec=Session)
        with pytest.raises(HTTPException) as exc_info:
            get_image_by_id(db, image_id=999, user_id=1)
        
        assert exc_info.value.status_code == 404


class TestDeleteImage:
    """Tests for delete_image function."""
    
    @patch('app.application.services.image_service.get_image_by_id')
    @patch('app.application.services.image_service.containers_repository')
    def test_delete_image_success(self, mock_containers_repo, mock_get_image):
        """Test successful image deletion."""
        # Setup mocks
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_get_image.return_value = mock_image
        mock_containers_repo.get_containers_by_image_id.return_value = []  # No containers
        
        db = Mock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()
        
        # Test
        delete_image(db, image_id=1, user_id=1)
        
        # Assertions
        mock_get_image.assert_called_once_with(db, 1, 1)
        db.delete.assert_called_once_with(mock_image)
        db.commit.assert_called_once()
    
    @patch('app.application.services.image_service.get_image_by_id')
    @patch('app.application.services.image_service.containers_repository')
    def test_delete_image_with_running_containers(self, mock_containers_repo, mock_get_image):
        """Test image deletion fails when containers are running."""
        # Setup mocks
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_get_image.return_value = mock_image
        
        mock_container = Mock()
        mock_container.status = ContainerStatus.RUNNING
        mock_containers_repo.get_containers_by_image_id.return_value = [mock_container]
        
        db = Mock(spec=Session)
        
        # Test
        with pytest.raises(HTTPException) as exc_info:
            delete_image(db, image_id=1, user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "running" in str(exc_info.value.detail).lower()

