import logging
from logging.handlers import TimedRotatingFileHandler
import json
import contextvars
import os
from datetime import datetime

from app.utils.config import LOG_LEVEL
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


class JSONFormatter(logging.Formatter):
    
    def format(self, record):
        # Campos internos de logging a excluir
        exclude_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName',
            'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'asctime'
        }
        
        dictionary = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno
        }
        
        
        correlation_id = correlation_id_var.get()
        if correlation_id is not None:
            dictionary["correlation_id"] = correlation_id
        
        for key, value in record.__dict__.items():
            if key not in exclude_fields:
                dictionary[key] = value
        
        json_string = json.dumps(dictionary)
        
        return json_string

class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        correlation_id = correlation_id_var.get() or "no-correlation-id"
        return f"{timestamp} [{record.levelname}] {record.name}: {record.getMessage()} (correlation_id={correlation_id})"
        


def setup_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

        os.makedirs("logs", exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            "logs/app.log",
            when='midnight',
            interval=1,
            backupCount=7 
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger
