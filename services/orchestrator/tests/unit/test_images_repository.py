"""
Unit tests for images_repository.
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.repositories import images_repository
from app.database.models import Image


@pytest.mark.unit
class TestImagesRepository:
    """Tests for images_repository functions."""
    
    def test_create(self):
        """Test creating an image."""
        mock_db = Mock(spec=Session)
        mock_image = Mock(spec=Image)
        
        result = images_repository.create(mock_db, mock_image)
        
        assert result == mock_image
        mock_db.add.assert_called_once_with(mock_image)
    
    def test_get_by_id_found(self):
        """Test getting image by ID when found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_image = Mock(spec=Image)
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_image
        
        result = images_repository.get_by_id(mock_db, image_id=1, user_id=1)
        
        assert result == mock_image
        mock_db.query.assert_called_once_with(Image)
    
    def test_get_by_id_not_found(self):
        """Test getting image by ID when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        result = images_repository.get_by_id(mock_db, image_id=999, user_id=1)
        
        assert result is None
    
    def test_get_all_images(self):
        """Test getting all images for a user."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_images = [Mock(spec=Image), Mock(spec=Image)]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_images
        
        result = images_repository.get_all_images(mock_db, user_id=1)
        
        assert result == mock_images
        assert len(result) == 2
    
    def test_get_all_images_empty(self):
        """Test getting all images when user has none."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        
        result = images_repository.get_all_images(mock_db, user_id=1)
        
        assert result == []
        assert len(result) == 0
    
    def test_get_all_images_with_containers(self):
        """Test getting all images with containers."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        mock_images = [Mock(spec=Image), Mock(spec=Image)]
        
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_images
        
        result = images_repository.get_all_images_with_containers(mock_db, user_id=1)
        
        assert result == mock_images
        assert len(result) == 2
    
    def test_get_by_app_hostname_found(self):
        """Test getting image by app_hostname when found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_image = Mock(spec=Image)
        mock_image.app_hostname = "example.com"
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_image
        
        result = images_repository.get_by_app_hostname(
            mock_db, 
            app_hostname="example.com", 
            user_id=1
        )
        
        assert result == mock_image
        assert result.app_hostname == "example.com"
    
    def test_get_by_app_hostname_not_found(self):
        """Test getting image by app_hostname when not found."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        result = images_repository.get_by_app_hostname(
            mock_db, 
            app_hostname="nonexistent.com", 
            user_id=1
        )
        
        assert result is None
