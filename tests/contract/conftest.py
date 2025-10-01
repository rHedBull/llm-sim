"""Pytest configuration for contract tests."""
from llm_sim.models.state import GlobalState

import logging
import structlog
import pytest


@pytest.fixture(autouse=True)
def configure_structlog(caplog):
    """Configure structlog to work with pytest's caplog fixture."""
    # Configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG,
        force=True  # Force reconfiguration
    )

    # Configure structlog to use standard library logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,  # Don't cache to allow reconfiguration
    )

    # Configure the root logger to DEBUG level
    logging.getLogger().setLevel(logging.DEBUG)

    # Ensure caplog captures at DEBUG level
    caplog.set_level(logging.DEBUG)