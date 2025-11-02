import logging
from logging.handlers import TimedRotatingFileHandler
import json
import contextvars
import os
import pathlib
from datetime import datetime

correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


class JSONFormatter(logging.Formatter):
    
    def format(self, record):
        json_string = json.dumps({
        "timestamp": datetime.fromtimestamp(record.created).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
        "correlation_id": correlation_id_var.get(),
        "filename": record.filename,
        "lineno": record.lineno
        })
        
        return json_string

class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).isoformat(),
        return f"{timestamp} [{record.levelname}] {record.name}: {record.getMessage()} (correlation_id={ correlation_id_var.get()})"
        


def setup_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

        os.makedirs("logs", exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            "logs/app.log",
            when='midnight',
            interval=1,
            backupCount=7  # Mantener 7 días
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger
