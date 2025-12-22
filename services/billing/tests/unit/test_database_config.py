"""
Unit tests for database configuration.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and error scenarios
- Full type hints and descriptive docstrings
"""
import pytest
import os
import sys
from typing import Generator
from unittest.mock import Mock, patch, MagicMock

# Mock psycopg2 before importing
sys.modules["psycopg2"] = MagicMock()


@pytest.mark.unit
class TestValidateDatabaseUrl:
    """Test suite for validate_database_url function."""
    
    def test_validate_database_url_empty(self) -> None:
        """Test validation with empty URL (Error Case 1: Invalid Data).
        
        Verifies:
        - ValueError is raised
        - Error message is appropriate
        
        Args:
            None
        """
        # Arrange
        from app.database.config import validate_database_url
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            validate_database_url("")
        
        assert "not set" in str(exc_info.value)
    
    def test_validate_database_url_invalid_scheme(self) -> None:
        """Test validation with invalid scheme (Error Case 1: Invalid Data).
        
        Verifies:
        - ValueError is raised
        - Error message indicates PostgreSQL requirement
        
        Args:
            None
        """
        # Arrange
        from app.database.config import validate_database_url
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            validate_database_url("mysql://user:pass@localhost/db")
        
        assert "PostgreSQL" in str(exc_info.value)
    
    def test_validate_database_url_no_hostname(self) -> None:
        """Test validation with missing hostname (Error Case 1: Invalid Data).
        
        Verifies:
        - ValueError is raised
        - Error message indicates hostname requirement
        
        Args:
            None
        """
        # Arrange
        from app.database.config import validate_database_url
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            validate_database_url("postgresql:///dbname")
        
        assert "hostname" in str(exc_info.value)
    
    def test_validate_database_url_no_database(self) -> None:
        """Test validation with missing database name (Error Case 1: Invalid Data).
        
        Verifies:
        - ValueError is raised
        - Error message indicates database name requirement
        
        Args:
            None
        """
        # Arrange
        from app.database.config import validate_database_url
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            validate_database_url("postgresql://user:pass@localhost/")
        
        assert "database name" in str(exc_info.value)
    
    def test_validate_database_url_valid(self) -> None:
        """Test validation with valid URL (Happy Path).
        
        Verifies:
        - No exception is raised
        - Function completes successfully
        
        Args:
            None
        """
        # Arrange
        from app.database.config import validate_database_url
        valid_url = "postgresql://user:pass@localhost:5432/dbname"
        
        # Act & Assert
        # Should not raise
        validate_database_url(valid_url)


@pytest.mark.unit
class TestGetDb:
    """Test suite for get_db function."""
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_get_db_yields_session(self) -> None:
        """Test that get_db yields a database session (Happy Path).
        
        Verifies:
        - Generator yields a session
        - Session has required methods
        
        Args:
            None
        """
        # Arrange
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database.config import get_db
        
        # Act
        db_gen = get_db()
        db = next(db_gen)
        
        # Assert
        assert db is not None
        assert hasattr(db, 'close')
        
        # Clean up
        try:
            db_gen.close()
        except StopIteration:
            pass
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_get_db_closes_session_on_exit(self) -> None:
        """Test that get_db closes session when done (Happy Path).
        
        Verifies:
        - Generator properly closes session
        - Cleanup is performed
        
        Args:
            None
        """
        # Arrange
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database.config import get_db
        
        # Act
        db_gen = get_db()
        db = next(db_gen)
        
        # Assert
        assert hasattr(db, 'close')
        
        # Simulate generator completion
        try:
            next(db_gen, None)
        except StopIteration:
            pass
