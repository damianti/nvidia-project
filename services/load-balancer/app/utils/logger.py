"""
Logging configuration for load-balancer service.

Provides structured logging with:
- Console output: Human-readable format for development
- File output: JSON format for production and log aggregation
- Correlation IDs: Track requests across services
- Structured data: Contextual information in extra parameter
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import json
import contextvars
import os
from datetime import datetime, timezone
from typing import Any, Dict

from app.utils.config import LOG_LEVEL

correlation_id_var = contextvars.ContextVar("correlation_id", default=None)

# Valid log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON with:
    - Standard fields: timestamp, level, logger, message, filename, lineno
    - Correlation ID: If available in context
    - Custom fields: From extra parameter
    - Exception info: If exc_info is True
    """

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.exclude_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "asctime",
        }

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value to JSON-compatible format.

        Handles:
        - Datetime objects -> ISO format strings
        - Sets -> Lists
        - Non-serializable objects -> String representation
        """
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, set):
            return list(value)
        try:
            json.dumps(value)  # Test if serializable
            return value
        except (TypeError, ValueError):
            return str(value)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        try:
            # Use UTC timezone for consistent timestamps
            timestamp = datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat()

            dictionary: Dict[str, Any] = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "service": self.service_name,
                "message": record.getMessage(),
                "filename": record.filename,
                "lineno": record.lineno,
                "function": record.funcName,
            }

            # Add correlation ID if available
            correlation_id = correlation_id_var.get()
            if correlation_id is not None:
                dictionary["correlation_id"] = correlation_id

            # Add exception info if present
            if record.exc_info:
                dictionary["exception"] = self.formatException(record.exc_info)

            # Add custom fields from extra parameter
            for key, value in record.__dict__.items():
                if key not in self.exclude_fields:
                    dictionary[key] = self._serialize_value(value)

            return json.dumps(dictionary, ensure_ascii=False)
        except Exception as e:
            # Fallback to basic format if JSON serialization fails
            return json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "logger": "logger",
                    "service": self.service_name,
                    "message": f"Log formatting error: {str(e)}",
                    "original_message": str(record.getMessage()),
                }
            )


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter.

    Format: timestamp [LEVEL] service: message (correlation_id=xxx)
    """

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output."""
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        correlation_id = correlation_id_var.get() or "no-correlation-id"
        level = record.levelname
        message = record.getMessage()

        return (
            f"{timestamp} [{level:8s}] {self.service_name}: {message} "
            f"(correlation_id={correlation_id})"
        )


def _validate_log_level(log_level: str) -> str:
    """
    Validate and normalize log level.

    Args:
        log_level: Log level string

    Returns:
        Valid uppercase log level

    Raises:
        ValueError: If log level is invalid
    """
    log_level_upper = log_level.upper()
    if log_level_upper not in VALID_LOG_LEVELS:
        raise ValueError(
            f"Invalid log level: {log_level}. "
            f"Valid levels: {', '.join(VALID_LOG_LEVELS)}"
        )
    return log_level_upper


def setup_logger(service_name: str) -> logging.Logger:
    """
    Set up logger with console and file handlers.

    Args:
        service_name: Name of the service (used in log output)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Get and validate log level
    try:
        log_level_str = _validate_log_level(LOG_LEVEL)
        log_level = getattr(logging, log_level_str)
    except (ValueError, AttributeError) as e:
        # Fallback to INFO if invalid
        print(f"Warning: Invalid LOG_LEVEL '{LOG_LEVEL}', using INFO. Error: {e}")
        log_level = logging.INFO

    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs from parent loggers

    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ConsoleFormatter(service_name))
    logger.addHandler(console_handler)

    # File handler (JSON format)
    os.makedirs("logs", exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        "logs/app.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter(service_name))
    logger.addHandler(file_handler)

    return logger
