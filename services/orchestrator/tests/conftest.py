import sys
import os
import pytest
from unittest.mock import MagicMock, Mock


def pytest_configure(config):
    """Hook que se ejecuta antes de importar los tests."""
    # Set DATABASE_URL before any imports that might need it
    os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/testdb')
    
    # Mock de psycopg2 antes de que app.database.models lo intente importar
    sys.modules["psycopg2"] = MagicMock()
    sys.modules["confluent_kafka"] = MagicMock()

@pytest.fixture
def db_session_mock():
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.refresh = Mock()
    db.flush = Mock()
    db.delete = Mock()
    return db