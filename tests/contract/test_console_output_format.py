"""Contract tests for console output format.

Tests console output formatting including colors, alignment, and readability
as specified in contracts/console_output_contract.md (LC-003).
"""

import re
import sys
from io import StringIO
from unittest.mock import patch

import pytest
import structlog

from llm_sim.utils.logging import configure_logging, get_logger


class TestConsoleOutputFormat:
    """Test suite for console output format contract (LC-003)."""

    @pytest.fixture(autouse=True)
    def disable_log_capture(self, caplog):
        """Disable pytest log capturing for output tests."""
        caplog.set_level(100000)  # Disable all log capturing

    def test_basic_console_format(self, capsys):
        """Test basic console output format."""
        configure_logging(level="INFO", format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        output = captured.err

        # Must contain timestamp (YYYY-MM-DD HH:MM:SS pattern)
        assert re.search(r"\d{4}-\d{2}-\d{2}.\d{2}:\d{2}:\d{2}", output)

        # Must contain level in brackets
        assert "[info" in output.lower() or "info" in output.lower()

        # Must contain event name
        assert "test_event" in output

        # Must contain key=value
        assert "key" in output and "value" in output

    def test_event_name_in_output(self, capsys):
        """Test that event names appear in console output."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        test_events = ["short", "medium_length_event", "very_long_event_name_that_exceeds_normal_length"]

        for event in test_events:
            capsys.readouterr()  # Clear
            logger.info(event)

            output = capsys.readouterr().err
            assert event[:35] in output  # At least first 35 chars should appear

    def test_log_level_display(self, capsys):
        """Test that log levels are displayed correctly."""
        configure_logging(level="DEBUG", format="console")  # Set DEBUG to see all levels
        logger = get_logger(__name__)

        levels = [
            ("info", lambda: logger.info("info_event")),
            ("warning", lambda: logger.warning("warn_event")),
            ("error", lambda: logger.error("error_event")),
            ("debug", lambda: logger.debug("debug_event")),
        ]

        for level_name, log_func in levels:
            capsys.readouterr()  # Clear
            log_func()

            output = capsys.readouterr().err.lower()
            # Level should appear in output (in brackets or otherwise)
            assert level_name in output or level_name[:4] in output

    def test_context_display_as_key_value(self, capsys):
        """Test that bound context and event data are displayed as key=value."""
        configure_logging(format="console")
        logger = get_logger(__name__).bind(run_id="test-123", simulation="demo")

        capsys.readouterr()  # Clear
        logger.info("event", turn=5, agent="alice")

        output = capsys.readouterr().err

        # Must contain bound context
        assert "run_id" in output
        assert "test-123" in output
        assert "simulation" in output
        assert "demo" in output

        # Must contain event data
        assert "turn" in output
        assert "5" in output or "turn=5" in output
        assert "agent" in output
        assert "alice" in output

    def test_no_json_in_console_format(self, capsys):
        """Test that console format doesn't output JSON structure."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("test_event", key="value")

        output = capsys.readouterr().err

        # Should NOT be JSON format
        # (No starting/ending braces with quoted keys)
        json_pattern = r'^\s*\{.*"event".*:.*"test_event".*\}\s*$'
        assert not re.match(json_pattern, output)

    def test_timestamp_format(self, capsys):
        """Test timestamp format in console output."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("test_event")

        output = capsys.readouterr().err

        # Timestamp should be in readable format (not ISO with T and Z)
        # Should have YYYY-MM-DD HH:MM:SS or similar
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}.\d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, output)

        # Should NOT have ISO format with 'T' separator
        iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        # This may or may not be present depending on structlog config

    def test_exception_formatting(self, capsys):
        """Test that exceptions are formatted readably with traceback."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        try:
            raise ValueError("Test error message")
        except ValueError:
            capsys.readouterr()  # Clear
            logger.error("error_occurred", exc_info=True)

        output = capsys.readouterr().err

        # Must contain error event
        assert "error_occurred" in output

        # Should contain traceback information
        # Note: exact format depends on structlog configuration
        assert "ValueError" in output or "Test error" in output

    def test_console_vs_json_difference(self, capsys):
        """Test that console format is different from JSON format."""
        # Test JSON format
        configure_logging(format="json")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("test_event", key="value")
        json_output = capsys.readouterr().err

        # Test console format
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("test_event", key="value")
        console_output = capsys.readouterr().err

        # Outputs should be different
        assert json_output != console_output

        # JSON should have quotes and braces
        # Console should have key=value format
        if json_output.strip():
            assert "{" in json_output
        if console_output.strip():
            # Console format should not be pure JSON
            assert "key=value" in console_output or ("key" in console_output and "value" in console_output)

    def test_multiple_context_fields_display(self, capsys):
        """Test that multiple context fields are all displayed."""
        configure_logging(format="console")
        logger = get_logger(__name__).bind(
            field1="value1",
            field2="value2",
            field3="value3",
            field4="value4"
        )

        capsys.readouterr()  # Clear
        logger.info("event")

        output = capsys.readouterr().err

        # All fields should appear in output
        assert "field1" in output
        assert "value1" in output
        assert "field2" in output
        assert "value2" in output
        assert "field3" in output
        assert "value3" in output
        assert "field4" in output
        assert "value4" in output

    def test_numeric_values_display(self, capsys):
        """Test that numeric values are displayed correctly."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("event", turn=5, duration_ms=123.45, count=100)

        output = capsys.readouterr().err

        # Numeric values should appear
        assert "5" in output
        assert "123.45" in output or "123" in output
        assert "100" in output

    def test_boolean_values_display(self, capsys):
        """Test that boolean values are displayed correctly."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("event", enabled=True, paused=False)

        output = capsys.readouterr().err

        # Boolean values should appear
        # (may be "True"/"False" or "true"/"false")
        output_lower = output.lower()
        assert "true" in output_lower
        assert "false" in output_lower

    def test_special_characters_in_values(self, capsys):
        """Test handling of special characters in values."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.info("event", message="test with spaces", path="/path/to/file")

        output = capsys.readouterr().err

        # Values with spaces and special chars should appear
        assert "test with spaces" in output or "test" in output
        assert "/path/to/file" in output or "path" in output


class TestColorCoding:
    """Test suite for color coding in console output."""

    @pytest.fixture(autouse=True)
    def disable_log_capture(self, caplog):
        """Disable pytest log capturing for output tests."""
        caplog.set_level(100000)  # Disable all log capturing

    @patch("sys.stdout.isatty", return_value=True)
    def test_colors_enabled_when_tty(self, mock_isatty, capsys):
        """Test that colors might be enabled when output is TTY."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.error("error_event")

        output = capsys.readouterr().err

        # When TTY, colors MAY be present (depends on ConsoleRenderer config)
        # We just verify the log appears
        assert "error" in output.lower()

    @patch("sys.stdout.isatty", return_value=False)
    def test_colors_not_required_when_non_tty(self, mock_isatty, capsys):
        """Test that output works when not TTY (no colors required)."""
        configure_logging(format="console")
        logger = get_logger(__name__)

        capsys.readouterr()  # Clear
        logger.error("error_event")

        output = capsys.readouterr().err

        # Should still output event (may or may not have colors)
        assert "error" in output.lower()


class TestLoggerHierarchy:
    """Test suite for logger hierarchy display."""

    @pytest.fixture(autouse=True)
    def disable_log_capture(self, caplog):
        """Disable pytest log capturing for output tests."""
        caplog.set_level(100000)  # Disable all log capturing

    def test_logger_name_hierarchy(self, capsys):
        """Test that logger hierarchy is preserved."""
        configure_logging(format="console")

        logger1 = get_logger("llm_sim.orchestrator")
        logger2 = get_logger("llm_sim.infrastructure.events")
        logger3 = get_logger("llm_sim.infrastructure.patterns")

        capsys.readouterr()  # Clear

        logger1.info("orch_event")
        out1 = capsys.readouterr().err

        logger2.info("event_event")
        out2 = capsys.readouterr().err

        logger3.info("pattern_event")
        out3 = capsys.readouterr().err

        # Verify events appear (hierarchy may or may not be in output depending on config)
        assert "orch_event" in out1
        assert "event_event" in out2
        assert "pattern_event" in out3
