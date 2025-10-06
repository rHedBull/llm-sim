# Contract: Logging Context Binding

**Feature**: 011-logging-improvements-enhanced
**Contract ID**: LC-002
**Date**: 2025-10-06

## Purpose

Define the contract for binding context to logger instances and ensuring context propagates through all log calls.

## API Signature

```python
class BoundLogger:
    def bind(self, **new_values) -> BoundLogger:
        """Create new logger with additional context merged.

        Args:
            **new_values: Key-value pairs to bind as context

        Returns:
            New BoundLogger instance with merged context

        Raises:
            ValueError: If any value is not JSON-serializable
        """

    def info(self, event: str, **event_data) -> None:
        """Log INFO level event with bound context + event data."""

    def debug(self, event: str, **event_data) -> None:
        """Log DEBUG level event with bound context + event data."""

    def warning(self, event: str, **event_data) -> None:
        """Log WARNING level event with bound context + event data."""

    def error(self, event: str, **event_data) -> None:
        """Log ERROR level event with bound context + event data."""
```

## Behavioral Contract

### Context Binding

**MUST return new logger instance**:
```python
logger = get_logger(__name__)
bound_logger = logger.bind(run_id="test-123")

assert logger is not bound_logger  # Different instances
```

**MUST NOT mutate original logger**:
```python
logger = get_logger(__name__)
bound_logger = logger.bind(run_id="test-123")

# Original logger unchanged
with capture_logs() as logs:
    logger.info("event")
    assert "run_id" not in logs[0]

# Bound logger has context
with capture_logs() as logs:
    bound_logger.info("event")
    assert logs[0]["run_id"] == "test-123"
```

**MUST merge context on successive binds**:
```python
logger = get_logger(__name__)
logger1 = logger.bind(key1="value1")
logger2 = logger1.bind(key2="value2")

# logger2 has both contexts
with capture_logs() as logs:
    logger2.info("event")
    assert logs[0]["key1"] == "value1"
    assert logs[0]["key2"] == "value2"
```

**MUST allow overriding context keys**:
```python
logger = get_logger(__name__)
logger1 = logger.bind(env="dev")
logger2 = logger1.bind(env="prod")  # Override

with capture_logs() as logs:
    logger2.info("event")
    assert logs[0]["env"] == "prod"  # Latest value wins
```

### Context Propagation

**MUST include bound context in all log calls**:
```python
logger = get_logger(__name__).bind(run_id="test-123", simulation="demo")

with capture_logs() as logs:
    logger.info("event1")
    logger.info("event2", extra="data")
    logger.warning("event3")

# All logs include bound context
assert all(log["run_id"] == "test-123" for log in logs)
assert all(log["simulation"] == "demo" for log in logs)
```

**MUST merge event_data with bound context**:
```python
logger = get_logger(__name__).bind(run_id="test-123")

with capture_logs() as logs:
    logger.info("event", turn=5, agent="alice")

log = logs[0]
assert log["run_id"] == "test-123"  # From bound context
assert log["turn"] == 5              # From event_data
assert log["agent"] == "alice"       # From event_data
```

**MUST prioritize event_data over bound context if key collision**:
```python
logger = get_logger(__name__).bind(value="from_context")

with capture_logs() as logs:
    logger.info("event", value="from_event")

# Event data takes precedence
assert logs[0]["value"] == "from_event"
```

### Async Context Propagation

**MUST propagate context through async calls** (when contextvars processor enabled):
```python
import asyncio
from structlog.contextvars import bind_contextvars

async def main():
    bind_contextvars(run_id="async-123")

    logger = get_logger(__name__)
    logger.info("main_event")  # Includes run_id

    await nested_async()

async def nested_async():
    logger = get_logger(__name__)
    logger.info("nested_event")  # Also includes run_id

# Both logs include run_id from context vars
```

## Orchestrator Binding Pattern

```python
class SimulationOrchestrator:
    def __init__(self, config, log_context=None):
        # Start with external context if provided
        logger = configure_logging(bind_context=log_context)

        # Bind orchestrator-specific context
        self.logger = logger.bind(
            run_id=self.run_id,
            simulation=config.simulation.name,
            component="orchestrator"
        )

    def run(self):
        # All logs include run_id + simulation + component
        self.logger.info("simulation_starting", num_agents=len(self.agents))
```

**Contract Assertions**:
- External context propagates to orchestrator logs ✅
- Orchestrator context added to external context ✅
- All orchestrator logs include full context ✅

## Agent Binding Pattern

```python
class Agent:
    def __init__(self, name: str):
        self.name = name
        # Bind agent_id to instance logger
        self.logger = get_logger(__name__).bind(
            agent_id=name,
            component="agent"
        )

    def decide_action(self, state):
        # All logs include agent_id + component
        self.logger.info("decision_started", turn=state.turn)
        # ...
        self.logger.info("decision_completed", action=action.type)
```

**Contract Assertions**:
- Agent instance logger includes agent_id ✅
- Multiple agents don't interfere with each other ✅
- Agent logs include component name ✅

## Error Conditions

### Non-Serializable Context Value

```python
import threading

logger = get_logger(__name__)

try:
    logger.bind(lock=threading.Lock())
except ValueError as e:
    assert "not JSON-serializable" in str(e)
```

### Invalid Context Key

```python
logger = get_logger(__name__)

# Keys with spaces or special chars may be rejected
try:
    logger.bind(**{"invalid key": "value"})
except (ValueError, TypeError):
    pass  # Expected to fail
```

## Test Scenarios

### Scenario 1: Basic Context Binding

```python
def test_basic_context_binding():
    """Test that bind() attaches context to logger."""
    logger = get_logger(__name__)
    bound_logger = logger.bind(run_id="test-123")

    with capture_logs() as logs:
        bound_logger.info("event")

    assert logs[0]["run_id"] == "test-123"
```

### Scenario 2: Immutability

```python
def test_logger_immutability():
    """Test that bind() doesn't mutate original logger."""
    logger = get_logger(__name__)
    bound_logger = logger.bind(key="value")

    with capture_logs() as logs:
        logger.info("original")
        bound_logger.info("bound")

    # Original logger has no context
    assert "key" not in logs[0]
    # Bound logger has context
    assert logs[1]["key"] == "value"
```

### Scenario 3: Context Merging

```python
def test_context_merging():
    """Test that successive binds merge context."""
    logger = get_logger(__name__)
    logger = logger.bind(key1="value1")
    logger = logger.bind(key2="value2")

    with capture_logs() as logs:
        logger.info("event")

    assert logs[0]["key1"] == "value1"
    assert logs[0]["key2"] == "value2"
```

### Scenario 4: Event Data Priority

```python
def test_event_data_priority():
    """Test that event data overrides bound context."""
    logger = get_logger(__name__).bind(value="context")

    with capture_logs() as logs:
        logger.info("event", value="event")

    # Event data takes precedence
    assert logs[0]["value"] == "event"
```

### Scenario 5: Multi-Logger Isolation

```python
def test_multi_logger_isolation():
    """Test that different bound loggers don't interfere."""
    logger1 = get_logger("logger1").bind(id="logger1")
    logger2 = get_logger("logger2").bind(id="logger2")

    with capture_logs() as logs:
        logger1.info("event1")
        logger2.info("event2")

    assert logs[0]["id"] == "logger1"
    assert logs[1]["id"] == "logger2"
```

### Scenario 6: Orchestrator Pattern

```python
def test_orchestrator_context_pattern():
    """Test orchestrator binding pattern."""
    external_context = {"request_id": "req-123"}
    logger = configure_logging(bind_context=external_context)
    orchestrator_logger = logger.bind(run_id="sim-456", component="orchestrator")

    with capture_logs() as logs:
        orchestrator_logger.info("simulation_starting")

    # Includes both external and orchestrator context
    assert logs[0]["request_id"] == "req-123"
    assert logs[0]["run_id"] == "sim-456"
    assert logs[0]["component"] == "orchestrator"
```

## Contract Tests Location

**File**: `tests/contract/test_logging_context_binding.py`

**Test Function Names**:
- `test_basic_context_binding()`
- `test_logger_immutability()`
- `test_context_merging()`
- `test_event_data_priority()`
- `test_multi_logger_isolation()`
- `test_orchestrator_context_pattern()`
- `test_agent_context_pattern()`
- `test_non_serializable_value_rejected()`

## Success Criteria

✅ All test scenarios pass
✅ Context binding is immutable
✅ Context merging works correctly
✅ Event data overrides bound context
✅ Multiple loggers are isolated
✅ Orchestrator/agent patterns work as designed

---

*Contract LC-002 - Ready for contract test implementation*
