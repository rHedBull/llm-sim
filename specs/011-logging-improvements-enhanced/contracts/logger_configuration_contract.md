# Contract: Logger Configuration API

**Feature**: 011-logging-improvements-enhanced
**Contract ID**: LC-001
**Date**: 2025-10-06

## Purpose

Define the contract for configuring the logging system with context binding and format selection.

## API Signature

```python
def configure_logging(
    level: str = "INFO",
    format: str = "json",
    bind_context: dict[str, Any] | None = None
) -> structlog.BoundLogger:
    """Configure structured logging with optional bound context.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ('json' or 'console')
        bind_context: Optional context to bind to returned logger

    Returns:
        Configured logger with bound context (if provided)

    Raises:
        ValueError: If level or format is invalid
        ValueError: If bind_context contains non-JSON-serializable values
    """
```

## Behavioral Contract

### Input Validation

**MUST reject invalid log levels**:
```python
configure_logging(level="INVALID")  # Raises ValueError
```

**MUST reject invalid formats**:
```python
configure_logging(format="xml")  # Raises ValueError
```

**MUST accept valid parameters**:
```python
logger = configure_logging(level="DEBUG", format="console")  # Success
logger = configure_logging()  # Success (uses defaults)
```

### Return Value

**MUST return BoundLogger instance**:
```python
logger = configure_logging()
assert isinstance(logger, structlog.BoundLogger)
```

**MUST return logger with bound context if provided**:
```python
logger = configure_logging(bind_context={"run_id": "test-123"})
# All logs from this logger include run_id
```

**MUST return logger without context if not provided**:
```python
logger = configure_logging()
# Logs from this logger have no pre-bound context
```

### Side Effects

**MUST configure global structlog settings**:
```python
configure_logging(level="INFO", format="json")
# Subsequent get_logger() calls use these settings
```

**MUST be idempotent**:
```python
logger1 = configure_logging(level="INFO")
logger2 = configure_logging(level="INFO")
# Both loggers work identically
```

### Format Selection

**MUST output JSON when format="json"**:
```python
configure_logging(format="json")
logger = get_logger(__name__)
logger.info("test_event", key="value")
# Output: {"event": "test_event", "level": "info", "key": "value", "timestamp": "..."}
```

**MUST output console format when format="console"**:
```python
configure_logging(format="console")
logger = get_logger(__name__)
logger.info("test_event", key="value")
# Output: 2025-10-06 09:08:33 [info     ] test_event                       key=value
```

### Level Filtering

**MUST filter logs below configured level**:
```python
configure_logging(level="INFO")
logger = get_logger(__name__)

logger.debug("debug_event")  # NOT output
logger.info("info_event")    # Output
logger.warning("warn_event") # Output
logger.error("error_event")  # Output
```

### Context Binding

**MUST bind provided context to logger**:
```python
logger = configure_logging(bind_context={"run_id": "abc-123", "env": "test"})
logger.info("event")
# Output includes: "run_id": "abc-123", "env": "test"
```

**MUST validate context values are JSON-serializable**:
```python
import threading
lock = threading.Lock()  # Not JSON-serializable

configure_logging(bind_context={"lock": lock})  # Raises ValueError
```

## Error Conditions

### Invalid Level

```python
try:
    configure_logging(level="TRACE")
except ValueError as e:
    assert "Invalid log level" in str(e)
```

### Invalid Format

```python
try:
    configure_logging(format="xml")
except ValueError as e:
    assert "Invalid format" in str(e)
```

### Non-Serializable Context

```python
try:
    configure_logging(bind_context={"obj": object()})
except ValueError as e:
    assert "not JSON-serializable" in str(e)
```

## Test Scenarios

### Scenario 1: Default Configuration

```python
def test_default_configuration():
    """Test configure_logging with all defaults."""
    logger = configure_logging()

    # Must return BoundLogger
    assert isinstance(logger, structlog.BoundLogger)

    # Must allow logging
    logger.info("test_event", data="value")  # Should not raise
```

### Scenario 2: Custom Level and Format

```python
def test_custom_level_and_format():
    """Test configure_logging with custom parameters."""
    logger = configure_logging(level="DEBUG", format="console")

    # Must allow debug logs
    logger.debug("debug_event")  # Should output

    # Must use console format (verified by output inspection)
```

### Scenario 3: Context Binding

```python
def test_context_binding():
    """Test that bind_context is attached to logger."""
    logger = configure_logging(bind_context={"run_id": "test-123"})

    # Capture log output
    with capture_logs() as logs:
        logger.info("event")

    # Must include bound context
    assert logs[0]["run_id"] == "test-123"
```

### Scenario 4: Error on Invalid Parameters

```python
def test_invalid_parameters():
    """Test that invalid parameters raise ValueError."""
    with pytest.raises(ValueError):
        configure_logging(level="INVALID")

    with pytest.raises(ValueError):
        configure_logging(format="xml")

    with pytest.raises(ValueError):
        configure_logging(bind_context={"obj": object()})
```

### Scenario 5: Multiple Calls (Idempotency)

```python
def test_idempotent_configuration():
    """Test that multiple configure_logging calls work."""
    logger1 = configure_logging(level="INFO")
    logger2 = configure_logging(level="INFO")

    # Both loggers should work
    logger1.info("event1")
    logger2.info("event2")
    # Should not raise errors
```

## Contract Tests Location

**File**: `tests/contract/test_logger_configuration.py`

**Test Function Names**:
- `test_default_configuration()`
- `test_custom_level_and_format()`
- `test_context_binding()`
- `test_invalid_parameters()`
- `test_idempotent_configuration()`
- `test_json_output_format()`
- `test_console_output_format()`
- `test_level_filtering()`

## Success Criteria

✅ All test scenarios pass
✅ Contract tests fail initially (TDD red phase)
✅ Implementation makes tests pass (TDD green phase)
✅ No regressions in existing logging behavior

---

*Contract LC-001 - Ready for contract test implementation*
