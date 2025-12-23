"""
Unit tests for image service.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError


from app.application.services.image_service import (
    create_image_from_upload,
    get_image_by_id,
    delete_image,
    get_all_images,
    get_all_images_with_containers,
)
from tests.fixtures.image_fixtures import image_create_factory
from tests.helpers.mocks import make_docker_build_fail
from app.schemas.image import ImageCreate
from app.database.models import Image, ContainerStatus


@pytest.mark.unit
class TestCreateImageFromUpload:
    """Tests for create_image_from_upload function."""

    @pytest.mark.asyncio
    @patch(
        "app.application.services.image_service.docker_service.build_image_from_context"
    )
    @patch("app.application.services.image_service.prepare_context")
    @patch("app.application.services.image_service.images_repository")
    async def test_create_image_from_upload_success(
        self, mock_repo, mock_prepare, mock_build
    ):
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

        result = await create_image_from_upload(db=db, data=data, file=file)

        assert result.id == 1
        mock_prepare.assert_called_once()
        mock_build.assert_called_once_with(
            "/tmp/root/context", "nvidia-app-u1-i1", "latest"
        )
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "app.application.services.image_service.docker_service.build_image_from_context"
    )
    @patch("app.application.services.image_service.prepare_context")
    @patch("app.application.services.image_service.images_repository")
    async def test_create_image_from_upload_duplicate_app_hostname(
        self, mock_repo, mock_prepare, mock_build
    ):
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
            await create_image_from_upload(db=db, data=data, file=file)

        assert exc_info.value.status_code == 400
        mock_prepare.assert_not_called()
        mock_build.assert_not_called()


@pytest.mark.unit
class TestGetImageById:
    """Tests for get_image_by_id function."""

    @patch("app.application.services.image_service.images_repository")
    def test_get_image_by_id_success(self, mock_repo):
        """Test successful image retrieval."""
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_repo.get_by_id.return_value = mock_image

        db = Mock(spec=Session)
        result = get_image_by_id(db, image_id=1, user_id=1)

        assert result == mock_image
        mock_repo.get_by_id.assert_called_once_with(db, 1, 1)

    @patch("app.application.services.image_service.images_repository")
    def test_get_image_by_id_not_found(self, mock_repo):
        """Test image retrieval when image doesn't exist."""
        mock_repo.get_by_id.return_value = None

        db = Mock(spec=Session)
        with pytest.raises(HTTPException) as exc_info:
            get_image_by_id(db, image_id=999, user_id=1)

        assert exc_info.value.status_code == 404


@pytest.mark.unit
class TestDeleteImage:
    """Tests for delete_image function."""

    @patch("app.application.services.image_service.get_image_by_id")
    @patch("app.application.services.image_service.containers_repository")
    def test_delete_image_success(self, mock_containers_repo, mock_get_image):
        """Test successful image deletion."""
        # Setup mocks
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_get_image.return_value = mock_image
        mock_containers_repo.get_containers_by_image_id.return_value = (
            []
        )  # No containers

        db = Mock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()

        # Test
        delete_image(db, image_id=1, user_id=1)

        # Assertions
        mock_get_image.assert_called_once_with(db, 1, 1)
        db.delete.assert_called_once_with(mock_image)
        db.commit.assert_called_once()

    @patch("app.application.services.image_service.get_image_by_id")
    @patch("app.application.services.image_service.containers_repository")
    def test_delete_image_with_running_containers(
        self, mock_containers_repo, mock_get_image
    ):
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

    @patch("app.application.services.image_service.get_image_by_id")
    @patch("app.application.services.image_service.containers_repository")
    def test_delete_image_with_stopped_containers(
        self, mock_containers_repo, mock_get_image
    ):
        """Test image deletion succeeds when containers are stopped."""
        # Setup mocks
        mock_image = Mock(spec=Image)
        mock_image.id = 1
        mock_image.app_hostname = "example.com"
        mock_get_image.return_value = mock_image

        # Containers exist but are stopped
        mock_container = Mock()
        mock_container.status = ContainerStatus.STOPPED
        mock_containers_repo.get_containers_by_image_id.return_value = [mock_container]

        db = Mock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()

        # Test - should succeed because containers are stopped
        delete_image(db, image_id=1, user_id=1)

        # Assertions
        mock_get_image.assert_called_once_with(db, 1, 1)
        db.delete.assert_called_once_with(mock_image)
        db.commit.assert_called_once()


@pytest.mark.unit
class TestCreateImageFromUploadBuildFailure:
    """Tests for build failure in create_image_from_upload."""

    @pytest.mark.asyncio
    @patch(
        "app.application.services.image_service.docker_service.build_image_from_context"
    )
    @patch("app.application.services.image_service.prepare_context")
    @patch("app.application.services.image_service.images_repository")
    async def test_build_failure(
        self, mock_repo, mock_prepare, mock_build, db_session_mock
    ):

        mock_repo.get_by_app_hostname.return_value = None
        mock_repo.create.side_effect = (
            lambda db, image_obj: setattr(image_obj, "id", 1) or image_obj
        )
        mock_prepare.return_value = ("/tmp/root", "/tmp/root/context")
        mock_build.side_effect = make_docker_build_fail()

        data = image_create_factory(app_hostname="example-build-fail.com")
        file = Mock()
        file.filename = "app.zip"

        with pytest.raises(HTTPException) as exc_info:
            await create_image_from_upload(db=db_session_mock, data=data, file=file)

        assert exc_info.value.status_code == 500
        assert "failed to create image" in str(exc_info.value.detail).lower()
        assert "docker build failed" in str(exc_info.value.detail).lower()

        mock_prepare.assert_called_once()
        mock_build.assert_called_once_with(
            "/tmp/root/context", "nvidia-app-u1-i1", "latest"
        )

        assert db_session_mock.commit.call_count >= 1


@pytest.mark.unit
class TestGetAllImages:
    """Tests for get_all_images function."""

    @patch("app.application.services.image_service.images_repository")
    def test_get_all_images_success(self, mock_repo):
        """Test successful retrieval of all images for a user."""
        # Setup: mock repository returns a list of images
        mock_images = [
            Mock(spec=Image, id=1, name="app1", app_hostname="app1.com"),
            Mock(spec=Image, id=2, name="app2", app_hostname="app2.com"),
        ]
        mock_repo.get_all_images.return_value = mock_images

        db = Mock(spec=Session)
        result = get_all_images(db, user_id=1)

        # Assertions
        assert result == mock_images
        assert len(result) == 2
        mock_repo.get_all_images.assert_called_once_with(db, 1)

    @patch("app.application.services.image_service.images_repository")
    def test_get_all_images_empty(self, mock_repo):
        """Test when user has no images."""
        mock_repo.get_all_images.return_value = []

        db = Mock(spec=Session)
        result = get_all_images(db, user_id=1)

        assert result == []
        assert len(result) == 0
        mock_repo.get_all_images.assert_called_once_with(db, 1)


@pytest.mark.unit
class TestGetAllImagesWithContainers:
    """Tests for get_all_images_with_containers function."""

    @patch("app.application.services.image_service.images_repository")
    def test_get_all_images_with_containers_success(self, mock_repo):
        """Test successful retrieval of images with containers."""
        mock_image1 = Mock(spec=Image, id=1, name="app1", app_hostname="app1.com")
        mock_image1.containers = [Mock(id=1), Mock(id=2)]
        mock_image2 = Mock(spec=Image, id=2, name="app2", app_hostname="app2.com")
        mock_image2.containers = []

        mock_images = [mock_image1, mock_image2]
        mock_repo.get_all_images_with_containers.return_value = mock_images

        db = Mock(spec=Session)
        result = get_all_images_with_containers(db, user_id=1)

        assert result == mock_images
        assert len(result) == 2
        mock_repo.get_all_images_with_containers.assert_called_once_with(db, 1)

    @patch("app.application.services.image_service.images_repository")
    def test_get_all_images_with_containers_empty(self, mock_repo):
        """Test when user has no images."""
        mock_repo.get_all_images_with_containers.return_value = []

        db = Mock(spec=Session)
        result = get_all_images_with_containers(db, user_id=1)

        assert result == []
        assert len(result) == 0
        mock_repo.get_all_images_with_containers.assert_called_once_with(db, 1)


@pytest.mark.unit
class TestImageCreateValidation:
    """Tests for ImageCreate schema validation."""

    def test_container_port_valid_range(self):
        """Test that valid container ports (1-65535) are accepted."""
        # Valid ports
        valid_data = image_create_factory(container_port=8080)
        assert valid_data.container_port == 8080

        valid_data = image_create_factory(container_port=1)
        assert valid_data.container_port == 1

        valid_data = image_create_factory(container_port=65535)
        assert valid_data.container_port == 65535

    def test_container_port_invalid_too_low(self):
        """Test that container_port < 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            image_create_factory(container_port=0)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("container_port",) for error in errors)

    def test_container_port_invalid_too_high(self):
        """Test that container_port > 65535 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            image_create_factory(container_port=65536)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("container_port",) for error in errors)

    def test_min_instances_greater_than_max_instances(self):
        """Test that min_instances > max_instances is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            image_create_factory(min_instances=5, max_instances=3)

        errors = exc_info.value.errors()
        # The validator raises ValueError, which Pydantic converts to ValidationError
        assert len(errors) > 0
        assert "min_instances must be <= max_instances" in str(exc_info.value)

    def test_min_instances_equal_to_max_instances(self):
        """Test that min_instances == max_instances is valid."""
        valid_data = image_create_factory(min_instances=3, max_instances=3)
        assert valid_data.min_instances == 3
        assert valid_data.max_instances == 3
