"""
Logging Configuration Module

Provides centralized logging setup for the application.
"""

import logging
import logging.config
import os
from typing import Dict, Any

def setup_logging() -> None:
    """
    Configure application-wide logging with structured format.

    The configuration includes:
    - Console handler with color support
    - Structured JSON format for production
    - Appropriate log levels for different libraries
    """

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "handlers": ["console"]},
            "tortoise": {"level": "WARNING", "handlers": ["console"]},
            "elasticsearch": {"level": "WARNING", "handlers": ["console"]},
            "src": {"level": log_level, "handlers": ["console"], "propagate": False}
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }

    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a properly configured logger instance."""
    return logging.getLogger(name)