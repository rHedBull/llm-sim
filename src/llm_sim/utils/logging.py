"""Logging configuration for the simulation."""

import json
import logging
import os
import sys
from typing import Any, TextIO

import structlog


class _ResilientPrintLogger:
    """A print logger that handles closed file descriptors gracefully."""

    def __init__(self, file: TextIO = None):
        """Initialize logger.

        Args:
            file: Output file (defaults to sys.stderr)
        """
        self._file = file or sys.stderr

    def msg(self, message: str) -> None:
        """Print message, handling closed files gracefully.

        Args:
            message: Message to print
        """
        try:
            # Try the configured file first
            if self._file and not self._file.closed:
                print(message, file=self._file, flush=True)
            else:
                # Fall back to current sys.stderr
                print(message, file=sys.stderr, flush=True)
        except (ValueError, OSError):
            # If all else fails, silently drop the message
            # This can happen in test teardown scenarios
            pass

    def __getattr__(self, name: str):
        """Forward all other methods to msg."""
        return self.msg


class _ResilientLoggerFactory:
    """Logger factory that creates resilient print loggers."""

    def __init__(self, file: TextIO = None):
        """Initialize factory.

        Args:
            file: Output file (defaults to sys.stderr)
        """
        self._file = file

    def __call__(self, *args):
        """Create a new logger instance."""
        return _ResilientPrintLogger(self._file)


def _make_filtering_processor(log_level: str):
    """Create a processor that filters events by log level."""
    min_level = getattr(logging, log_level.upper())
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def filter_by_level(logger, method_name: str, event_dict):
        """Filter events based on configured log level."""
        event_level = level_map.get(method_name.lower(), logging.INFO)
        if event_level < min_level:
            raise structlog.DropEvent
        return event_dict

    return filter_by_level


def configure_logging(
    level: str = "INFO",
    format: str = "json",
    bind_context: dict[str, Any] | None = None
) -> structlog.BoundLogger:
    """Configure structured logging for the simulation.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ('json', 'console', or 'auto')
        bind_context: Optional context to bind to returned logger

    Returns:
        Configured logger with bound context (if provided)

    Raises:
        ValueError: If level or format is invalid
        ValueError: If bind_context contains non-JSON-serializable values
    """
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    if level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log level: {level}. Must be one of {valid_levels}"
        )

    # Validate format
    valid_formats = ["json", "console", "auto"]
    if format not in valid_formats:
        raise ValueError(
            f"Invalid format: {format}. Must be one of {valid_formats}"
        )

    # Auto-detect format based on environment
    if format == "auto":
        env = os.getenv("ENVIRONMENT", "development")
        format = "json" if env == "production" else "console"

    # Validate bind_context if provided
    if bind_context is not None:
        _validate_context(bind_context)

    # Build processor list
    processors = [
        structlog.contextvars.merge_contextvars,  # Enable contextvars support
        _make_filtering_processor(level),  # Filter by log level
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add output processor based on format
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                pad_event=35,
            )
        )

    # Configure structlog
    # Use ResilientLoggerFactory for stderr output that handles closed files
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=_ResilientLoggerFactory(file=sys.stderr),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get base logger
    logger = structlog.get_logger()

    # Bind context if provided
    if bind_context:
        logger = logger.bind(**bind_context)

    return logger


def _validate_context(context: dict[str, Any]) -> None:
    """Validate that context dictionary contains only JSON-serializable values.

    Args:
        context: Context dictionary to validate

    Raises:
        ValueError: If any value is not JSON-serializable
    """
    for key, value in context.items():
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Context value for '{key}' is not JSON-serializable: {value}"
            ) from e


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)
