"""Structured logging configuration with OpenTelemetry context correlation."""

import logging
import sys
import time
from typing import Final

from opentelemetry import trace
from pythonjsonlogger.json import JsonFormatter

from hybrid_observability.config import Settings

_LOG_FORMAT: Final = (
    "%(asctime)s "
    "%(levelname)s "
    "%(name)s "
    "%(message)s "
    "%(service_name)s "
    "%(service_version)s "
    "%(deployment_environment)s "
    "%(trace_id)s "
    "%(span_id)s"
)


class ObservabilityContextFilter(logging.Filter):
    """Add service metadata and active trace context to each log record."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._service_name = settings.service_name
        self._service_version = settings.service_version
        self._deployment_environment = settings.deployment_environment

    def filter(self, record: logging.LogRecord) -> bool:
        """Enrich a log record with service and OpenTelemetry attributes."""

        span_context = trace.get_current_span().get_span_context()

        record.service_name = self._service_name
        record.service_version = self._service_version
        record.deployment_environment = self._deployment_environment

        if span_context.is_valid:
            record.trace_id = format(span_context.trace_id, "032x")
            record.span_id = format(span_context.span_id, "016x")
        else:
            record.trace_id = None
            record.span_id = None

        return True


def configure_logging(settings: Settings) -> None:
    """Configure application and Uvicorn loggers for structured output."""

    formatter = JsonFormatter(
        _LOG_FORMAT,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "severity",
            "name": "logger",
        },
        timestamp=False,
    )
    formatter.converter = time.gmtime

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(ObservabilityContextFilter(settings))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    logging.captureWarnings(True)


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger for the requested module."""

    return logging.getLogger(name)
