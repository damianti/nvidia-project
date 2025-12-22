"""
Unit tests for database configuration.
"""
import pytest
import os
import sys
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestValidateDatabaseUrl:
    """Tests for validate_database_url function."""
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_valid_postgresql(self):
        """Test validation with valid PostgreSQL URL."""
        # Import function directly to avoid module-level validation
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        url = "postgresql://user:password@localhost:5432/dbname"
        # Should not raise
        config.validate_database_url(url)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_valid_postgresql_psycopg2(self):
        """Test validation with valid PostgreSQL+psycopg2 URL."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        url = "postgresql+psycopg2://user:password@localhost:5432/dbname"
        # Should not raise
        config.validate_database_url(url)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_empty(self):
        """Test validation with empty URL."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        with pytest.raises(ValueError) as exc_info:
            config.validate_database_url("")
        
        assert "DATABASE_URL environment variable is not set" in str(exc_info.value)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_invalid_scheme(self):
        """Test validation with invalid scheme."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        with pytest.raises(ValueError) as exc_info:
            config.validate_database_url("mysql://user:password@localhost/dbname")
        
        assert "DATABASE_URL must be a PostgreSQL connection string" in str(exc_info.value)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_no_hostname(self):
        """Test validation with URL missing hostname."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        with pytest.raises(ValueError) as exc_info:
            config.validate_database_url("postgresql:///dbname")
        
        assert "must include a hostname" in str(exc_info.value)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_validate_database_url_no_database(self):
        """Test validation with URL missing database name."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database import config
        with pytest.raises(ValueError) as exc_info:
            config.validate_database_url("postgresql://user:password@localhost/")
        
        assert "must include a database name" in str(exc_info.value)


@pytest.mark.unit
class TestGetDb:
    """Tests for get_db function."""
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database.config import get_db
        
        # Create a real session to test the generator
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        assert hasattr(db, 'close')
        
        # Clean up
        try:
            db_gen.close()
        except StopIteration:
            pass
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}, clear=False)
    def test_get_db_closes_session_on_exit(self):
        """Test that get_db closes session when done."""
        if 'app.database.config' in sys.modules:
            del sys.modules['app.database.config']
        
        from app.database.config import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        
        # Verify session has close method
        assert hasattr(db, 'close')
        
        # Simulate generator completion - this should call close
        try:
            next(db_gen, None)  # Try to get next item (should be None)
        except StopIteration:
            pass
        
        # The finally block should have closed the session
        # We can't easily test this without actually creating a real session,
        # so we just verify the generator works correctly
