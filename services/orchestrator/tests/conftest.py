import sys
import pytest
from unittest.mock import MagicMock, Mock


def pytest_configure(config):
    """Hook que se ejecuta antes de importar los tests."""
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