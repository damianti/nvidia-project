"""
Unit tests for dependency functions.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""
import pytest
from fastapi import HTTPException, Header
from fastapi.testclient import TestClient

from app.utils.dependencies import get_user_id


@pytest.mark.unit
class TestGetUserId:
    """Test suite for get_user_id dependency function."""
    
    def test_get_user_id_success(self) -> None:
        """Test successful user ID extraction (Happy Path).
        
        Verifies:
        - Valid user ID is returned as integer
        - Function works correctly
        
        Args:
            None
        """
        # Arrange
        x_user_id = "123"
        
        # Act
        result = get_user_id(x_user_id=x_user_id)
        
        # Assert
        assert result == 123
        assert isinstance(result, int)
    
    def test_get_user_id_invalid_string(self) -> None:
        """Test user ID extraction with invalid string (Error Case 1: Invalid Data).
        
        Verifies:
        - HTTPException is raised
        - Status code is 400
        - Error message is appropriate
        
        Args:
            None
        """
        # Arrange
        x_user_id = "invalid"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_user_id(x_user_id=x_user_id)
        
        assert exc_info.value.status_code == 400
        assert "Invalid user_id" in exc_info.value.detail
    
    def test_get_user_id_empty_string(self) -> None:
        """Test user ID extraction with empty string (Error Case 1: Invalid Data).
        
        Verifies:
        - HTTPException is raised
        - Status code is 400
        
        Args:
            None
        """
        # Arrange
        x_user_id = ""
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_user_id(x_user_id=x_user_id)
        
        assert exc_info.value.status_code == 400
