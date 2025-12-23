"""
Unit tests for containers_repository.
"""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.repositories import containers_repository
from app.database.models import Container


@pytest.mark.unit
class TestContainersRepository:
    """Tests for containers_repository functions."""

    def test_create(self):
        """Test creating a container."""
        mock_db = Mock(spec=Session)
        mock_container = Mock(spec=Container)

        result = containers_repository.create(mock_db, mock_container)

        assert result == mock_container
        mock_db.add.assert_called_once_with(mock_container)

    def test_get_by_id_and_user_found(self):
        """Test getting container by ID and user when found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_container = Mock(spec=Container)
        mock_container.id = 1
        mock_container.user_id = 1

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_container

        result = containers_repository.get_by_id_and_user(
            mock_db, container_id=1, user_id=1
        )

        assert result == mock_container
        assert result.id == 1
        assert result.user_id == 1

    def test_get_by_id_and_user_not_found(self):
        """Test getting container by ID and user when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        result = containers_repository.get_by_id_and_user(
            mock_db, container_id=999, user_id=1
        )

        assert result is None

    def test_get_containers_by_image_id(self):
        """Test getting containers by image ID."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_containers = [Mock(spec=Container), Mock(spec=Container)]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_containers

        result = containers_repository.get_containers_by_image_id(mock_db, image_id=1)

        assert result == mock_containers
        assert len(result) == 2

    def test_get_containers_by_image_id_empty(self):
        """Test getting containers by image ID when none exist."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        result = containers_repository.get_containers_by_image_id(mock_db, image_id=999)

        assert result == []
        assert len(result) == 0

    def test_list_by_user(self):
        """Test listing containers by user."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_containers = [
            Mock(spec=Container),
            Mock(spec=Container),
            Mock(spec=Container),
        ]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_containers

        result = containers_repository.list_by_user(mock_db, user_id=1)

        assert result == mock_containers
        assert len(result) == 3

    def test_list_by_user_empty(self):
        """Test listing containers by user when user has none."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        result = containers_repository.list_by_user(mock_db, user_id=999)

        assert result == []
        assert len(result) == 0

    def test_list_by_image_and_user(self):
        """Test listing containers by image and user."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_containers = [Mock(spec=Container), Mock(spec=Container)]

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_containers

        result = containers_repository.list_by_image_and_user(
            mock_db, image_id=1, user_id=1
        )

        assert result == mock_containers
        assert len(result) == 2

    def test_list_by_image_and_user_empty(self):
        """Test listing containers by image and user when none exist."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        result = containers_repository.list_by_image_and_user(
            mock_db, image_id=999, user_id=1
        )

        assert result == []
        assert len(result) == 0
