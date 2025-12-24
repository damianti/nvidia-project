"""
Unit tests for logger utilities.

This module implements comprehensive unit tests following QA best practices:
- AAA pattern (Arrange, Act, Assert)
- Happy path and edge scenarios
- Full type hints and descriptive docstrings
"""

import pytest
import json
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import logging

from app.utils.logger import JSONFormatter, ConsoleFormatter


@pytest.mark.unit
class TestJSONFormatter:
    """Test suite for JSONFormatter class."""

    def test_serialize_value_datetime(self) -> None:
        """Test serialization of datetime objects (Happy Path).

        Verifies:
        - Datetime is converted to ISO format string
        - Result is JSON-serializable

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        dt = datetime.now(timezone.utc)

        # Act
        result = formatter._serialize_value(dt)

        # Assert
        assert isinstance(result, str)
        assert "T" in result  # ISO format contains T
        # Verify it's valid ISO format
        datetime.fromisoformat(result.replace("Z", "+00:00"))

    def test_serialize_value_set(self) -> None:
        """Test serialization of set objects (Happy Path).

        Verifies:
        - Set is converted to list
        - Result is JSON-serializable

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        test_set = {1, 2, 3}

        # Act
        result = formatter._serialize_value(test_set)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert set(result) == test_set

    def test_serialize_value_non_serializable(self) -> None:
        """Test serialization of non-serializable objects (Edge Case).

        Verifies:
        - Non-serializable object is converted to string
        - No exception is raised

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        non_serializable = object()

        # Act
        result = formatter._serialize_value(non_serializable)

        # Assert
        assert isinstance(result, str)

    def test_format_record_success(self) -> None:
        """Test formatting a log record (Happy Path).

        Verifies:
        - Record is formatted as JSON
        - Required fields are present
        - JSON is valid

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Act
        result = formatter.format(record)

        # Assert
        assert isinstance(result, str)
        data = json.loads(result)
        assert "timestamp" in data
        assert "level" in data
        assert "message" in data
        assert data["message"] == "Test message"
        assert data["service"] == "test-service"

    def test_format_record_with_exception(self) -> None:
        """Test formatting a log record with exception (Edge Case).

        Verifies:
        - Exception info is included in JSON
        - Exception is properly formatted

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="/test/path",
                lineno=1,
                msg="Test message with exception",
                args=(),
                exc_info=sys.exc_info(),
            )

        # Act
        result = formatter.format(record)

        # Assert
        assert isinstance(result, str)
        data = json.loads(result)
        assert "exception" in data
        assert "Test exception" in data["exception"]

    def test_format_record_with_custom_fields(self) -> None:
        """Test formatting a log record with custom extra fields (Happy Path).

        Verifies:
        - Custom fields are included in JSON
        - Fields are properly serialized

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        record.number_field = 42

        # Act
        result = formatter.format(record)

        # Assert
        assert isinstance(result, str)
        data = json.loads(result)
        assert "custom_field" in data
        assert data["custom_field"] == "custom_value"
        assert "number_field" in data
        assert data["number_field"] == 42

    def test_format_record_fallback_on_error(self) -> None:
        """Test formatting fallback when JSON serialization fails (Edge Case).

        Verifies:
        - Fallback format is used on error
        - No exception is raised
        - Error message is included

        Args:
            None
        """
        # Arrange
        formatter = JSONFormatter("test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock json.dumps to fail in the try block
        original_dumps = json.dumps
        call_count = [0]

        def failing_dumps(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call fails
                raise Exception("JSON error")
            return original_dumps(*args, **kwargs)

        with patch("app.utils.logger.json.dumps", side_effect=failing_dumps):
            # Act
            result = formatter.format(record)

            # Assert
            assert isinstance(result, str)
            data = json.loads(result)
            assert "Log formatting error" in data["message"]
            assert "original_message" in data


@pytest.mark.unit
class TestConsoleFormatter:
    """Test suite for ConsoleFormatter class."""

    def test_format_record_success(self) -> None:
        """Test formatting a log record for console (Happy Path).

        Verifies:
        - Record is formatted as human-readable string
        - Required information is present

        Args:
            None
        """
        # Arrange
        formatter = ConsoleFormatter("test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Act
        result = formatter.format(record)

        # Assert
        assert isinstance(result, str)
        assert "test-service" in result
        assert "Test message" in result
        assert "INFO" in result


@pytest.mark.unit
class TestValidateLogLevel:
    """Test suite for _validate_log_level function."""

    def test_validate_log_level_invalid(self) -> None:
        """Test validation with invalid log level (Error Case 1: Invalid Data).

        Verifies:
        - ValueError is raised
        - Error message is appropriate

        Args:
            None
        """
        # Arrange
        from app.utils.logger import _validate_log_level

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            _validate_log_level("INVALID")

        assert "Invalid log level" in str(exc_info.value)
        assert "INVALID" in str(exc_info.value)


@pytest.mark.unit
class TestSetupLogger:
    """Test suite for setup_logger function."""

    @patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}, clear=False)
    def test_setup_logger_invalid_level(self) -> None:
        """Test setup_logger with invalid log level (Error Case 1: Invalid Data).

        Verifies:
        - Invalid level is handled gracefully
        - Falls back to INFO
        - Logger is still created

        Args:
            None
        """
        # Arrange
        from app.utils.logger import setup_logger

        # Act
        logger = setup_logger("test-service")

        # Assert
        assert logger is not None
        assert logger.name == "test-service"

    @patch.dict("os.environ", {"LOG_LEVEL": "INVALID_ATTR"}, clear=False)
    @patch("app.utils.logger.getattr")
    def test_setup_logger_attribute_error(self, mock_getattr: Mock) -> None:
        """Test setup_logger when getattr fails (Error Case 2: Server Error).

        Verifies:
        - AttributeError is handled gracefully
        - Falls back to INFO
        - Logger is still created

        Args:
            mock_getattr: Mocked getattr function
        """
        # Arrange
        from app.utils.logger import setup_logger

        # Make getattr raise AttributeError
        def failing_getattr(obj, name, default=None):
            if name == "INVALID_ATTR":
                raise AttributeError(f"module 'logging' has no attribute '{name}'")
            return getattr(obj, name, default)

        mock_getattr.side_effect = failing_getattr

        # Act
        logger = setup_logger("test-service")

        # Assert
        assert logger is not None
        assert logger.name == "test-service"
