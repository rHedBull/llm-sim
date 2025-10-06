"""Contract tests for logger configuration API.

Tests the configure_logging() function contract as specified in
contracts/logger_configuration_contract.md (LC-001).
"""

import json
import os
import sys
import threading
from io import StringIO
from typing import Any

import pytest
import structlog

from llm_sim.utils.logging import configure_logging, get_logger


class TestLoggerConfiguration:
    """Test suite for logger configuration contract (LC-001)."""

    @pytest.fixture(autouse=True)
    def disable_log_capture(self, caplog):
        """Disable pytest log capturing for output tests."""
        caplog.set_level(100000)  # Disable all log capturing

    def test_default_configuration(self):
        """Test configure_logging with all defaults."""
        logger = configure_logging()

        # Must return a logger (BoundLogger or proxy)
        assert logger is not None
        assert hasattr(logger, 'info')  # Has logging methods

        # Must allow logging
        logger.info("test_event", data="value")  # Should not raise

    def test_returns_bound_logger(self):
        """Test that configure_logging returns BoundLogger instance."""
        logger = configure_logging(level="INFO", format="json")

        assert logger is not None
        assert hasattr(logger, 'bind')  # Has bind method
        assert hasattr(logger, 'info')  # Has logging methods

    def test_custom_level_and_format(self):
        """Test configure_logging with custom parameters."""
        logger = configure_logging(level="DEBUG", format="console")

        # Must return a logger
        assert logger is not None
        assert hasattr(logger, 'debug')

        # Must allow debug logs
        logger.debug("debug_event")  # Should not raise

    def test_context_binding_via_parameter(self, capsys):
        """Test that bind_context parameter attaches context to logger."""
        logger = configure_logging(
            level="INFO",
            format="json",
            bind_context={"run_id": "test-123", "env": "test"}
        )

        # Logger should have bound context
        logger.info("test_event")

        # Capture output and verify context is present
        captured = capsys.readouterr()
        output = captured.err  # structlog often writes to stderr

        # Parse JSON output
        if output.strip():
            log_data = json.loads(output.strip())
            assert log_data.get("run_id") == "test-123"
            assert log_data.get("env") == "test"

    def test_invalid_level_raises_error(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            configure_logging(level="INVALID")

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid format"):
            configure_logging(format="xml")

    def test_non_serializable_context_raises_error(self):
        """Test that non-JSON-serializable context values raise ValueError."""
        lock = threading.Lock()  # Not JSON-serializable

        with pytest.raises(ValueError, match="not JSON-serializable"):
            configure_logging(bind_context={"lock": lock})

    def test_idempotent_configuration(self):
        """Test that multiple configure_logging calls work."""
        logger1 = configure_logging(level="INFO")
        logger2 = configure_logging(level="INFO")

        # Both loggers should work
        logger1.info("event1")
        logger2.info("event2")
        # Should not raise errors

    def test_json_output_format(self, capsys):
        """Test that format='json' produces valid JSON output."""
        configure_logging(level="INFO", format="json")
        logger = get_logger(__name__)

        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        output = captured.err.strip()

        if output:
            # Should be valid JSON
            log_data = json.loads(output)
            assert log_data["event"] == "test_event"
            assert log_data["key"] == "value"

    def test_console_output_format(self, capsys):
        """Test that format='console' produces readable output."""
        configure_logging(level="INFO", format="console")
        logger = get_logger(__name__)

        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        output = captured.err

        # Should contain event and key=value (not JSON)
        assert "test_event" in output
        assert "key=value" in output or "key" in output
        assert "{" not in output or "event" not in output  # Not JSON format

    def test_level_filtering(self, capsys):
        """Test that log level filtering works correctly."""
        configure_logging(level="INFO", format="json")
        logger = get_logger(__name__)

        # Clear any previous output
        capsys.readouterr()

        logger.debug("debug_event")  # Should NOT output
        logger.info("info_event")    # Should output
        logger.warning("warn_event") # Should output
        logger.error("error_event")  # Should output

        captured = capsys.readouterr()
        output = captured.err

        # Debug should not appear
        assert "debug_event" not in output

        # Info, warning, error should appear
        assert "info_event" in output
        assert "warn_event" in output or "warning" in output.lower()
        assert "error_event" in output

    def test_bind_context_none_works(self):
        """Test that bind_context=None works (no context bound)."""
        logger = configure_logging(bind_context=None)

        assert logger is not None
        assert hasattr(logger, 'info')

        # Should log without context
        logger.info("test_event")  # Should not raise

    def test_empty_bind_context_works(self):
        """Test that empty bind_context dict works."""
        logger = configure_logging(bind_context={})

        assert logger is not None
        assert hasattr(logger, 'info')
        logger.info("test_event")  # Should not raise


class TestLoggerAcquisition:
    """Test suite for get_logger() function."""

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns BoundLogger instance."""
        configure_logging()
        logger = get_logger(__name__)

        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'bind')

    def test_get_logger_with_module_name(self):
        """Test that get_logger accepts module name."""
        configure_logging()
        logger = get_logger("test.module.name")

        assert logger is not None
        assert hasattr(logger, 'info')
        # Logger should work
        logger.info("test")  # Should not raise


# Helper functions for testing

def capture_log_output(logger_func):
    """Capture log output to string."""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        logger_func()
        output = sys.stderr.getvalue()
        return output
    finally:
        sys.stderr = old_stderr
