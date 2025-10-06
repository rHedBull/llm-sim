# Quickstart: Enhanced Logging

**Feature**: 011-logging-improvements-enhanced
**Date**: 2025-10-06

## Overview

This guide shows developers how to use the enhanced logging features with context binding, improved console output, and external correlation support.

## Basic Usage

### 1. Simple Logging (No Context)

```python
from llm_sim.utils.logging import get_logger

# Get module-level logger
logger = get_logger(__name__)

# Log events
logger.info("simulation_starting", num_agents=5, max_turns=100)
logger.debug("processing_config", config_file="demo.yaml")
logger.warning("slow_operation", duration_ms=1543.2)
logger.error("validation_failed", reason="invalid_action")
```

**Output (console mode)**:
```
2025-10-06 09:08:33 [info     ] simulation_starting              num_agents=5 max_turns=100
2025-10-06 09:08:33 [debug    ] processing_config                config_file=demo.yaml
2025-10-06 09:08:34 [warning  ] slow_operation                   duration_ms=1543.2
2025-10-06 09:08:35 [error    ] validation_failed                reason=invalid_action
```

---

## Context Binding

### 2. Bind Context to Logger

```python
from llm_sim.utils.logging import get_logger

# Get base logger
logger = get_logger(__name__)

# Bind context - returns NEW logger with context
bound_logger = logger.bind(
    run_id="demo-20251006-090833",
    simulation="economic-sim"
)

# All logs from bound_logger include context automatically
bound_logger.info("simulation_starting", num_agents=5)
bound_logger.info("turn_completed", turn=1)
```

**Output**:
```
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-20251006-090833 simulation=economic-sim num_agents=5
2025-10-06 09:08:34 [info     ] turn_completed                   run_id=demo-20251006-090833 simulation=economic-sim turn=1
```

**Key Points**:
- `.bind()` returns a NEW logger instance (immutable)
- Original logger is unchanged
- Bound context appears in ALL subsequent log calls

---

## Orchestrator Pattern

### 3. Orchestrator with External Context

```python
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.utils.logging import configure_logging

# External system (e.g., API server) provides correlation context
external_context = {
    "request_id": "req-abc-123",
    "user_id": "user-456"
}

# Create orchestrator with external context
orchestrator = SimulationOrchestrator.from_yaml(
    path="config.yaml",
    log_context=external_context  # Inject external correlation
)

# Run simulation - all logs include external + orchestrator context
result = orchestrator.run()
```

**Orchestrator logs include**:
- External context: `request_id`, `user_id`
- Orchestrator context: `run_id`, `simulation_name`, `component`

**Output**:
```
2025-10-06 09:08:33 [info     ] simulation_starting              request_id=req-abc-123 user_id=user-456 run_id=demo-20251006 simulation=economic component=orchestrator num_agents=5
```

---

## Agent Pattern

### 4. Agent with Instance Context

```python
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.utils.logging import get_logger

class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)

        # Bind agent_id to instance logger
        self.logger = get_logger(__name__).bind(
            agent_id=self.name,
            component="agent"
        )

    def decide_action(self, state):
        # All logs include agent_id + component automatically
        self.logger.info("decision_started", turn=state.turn)

        # ... decision logic ...

        self.logger.info("decision_completed", action=action.type)
        return action
```

**Output**:
```
2025-10-06 09:08:34 [info     ] decision_started                 agent_id=alice component=agent turn=5
2025-10-06 09:08:34 [info     ] decision_completed               agent_id=alice component=agent action=trade
```

**Benefits**:
- Each agent instance has its own logger with bound context
- No need to pass `agent_id` on every log call
- Logs from different agents are easily distinguished

---

## Configuration

### 5. Configure Logging Format

```python
from llm_sim.utils.logging import configure_logging

# Console format (development)
configure_logging(level="DEBUG", format="console")
# Output: Readable console with colors and alignment

# JSON format (production)
configure_logging(level="INFO", format="json")
# Output: {"timestamp": "...", "level": "info", "event": "...", ...}

# Auto-detect (default)
configure_logging(level="INFO", format="auto")
# Uses "console" in development, "json" if ENVIRONMENT=production
```

### 6. Configure with Initial Context

```python
from llm_sim.utils.logging import configure_logging

# Configure with context bound to all loggers
logger = configure_logging(
    level="INFO",
    format="console",
    bind_context={
        "environment": "staging",
        "version": "1.0.0"
    }
)

# All logs include environment + version
logger.info("app_starting")
# Output includes: environment=staging version=1.0.0
```

---

## Advanced Patterns

### 7. Nested Context Binding

```python
from llm_sim.utils.logging import get_logger

# Start with base logger
logger = get_logger(__name__)

# Add orchestrator context
orch_logger = logger.bind(run_id="demo-123", simulation="economic")

# Add turn context for turn-specific operations
turn_logger = orch_logger.bind(turn=5)

# Logs include all context
turn_logger.info("turn_started", active_agents=5)
# Output: run_id=demo-123 simulation=economic turn=5 active_agents=5
```

### 8. Turn-Scoped Logging

```python
class SimulationOrchestrator:
    def _run_turn(self, state):
        # Create turn-scoped logger
        turn_logger = self.logger.bind(
            turn=state.turn,
            active_agents=len([a for a in self.agents if not a.paused]),
            paused_agents=len([a for a in self.agents if a.paused])
        )

        turn_logger.info("turn_started")

        # ... turn logic ...

        turn_logger.info("turn_completed", events=len(events))
```

**Output**:
```
2025-10-06 09:08:33 [info     ] turn_started                     run_id=demo-123 simulation=economic turn=5 active_agents=5 paused_agents=0
2025-10-06 09:08:34 [info     ] turn_completed                   run_id=demo-123 simulation=economic turn=5 active_agents=5 paused_agents=0 events=15
```

### 9. Exception Logging

```python
from llm_sim.utils.logging import get_logger

logger = get_logger(__name__)

try:
    result = risky_operation()
except ValueError as e:
    logger.error(
        "operation_failed",
        operation="risky_operation",
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True  # Include full traceback
    )
    raise
```

**Output**:
```
2025-10-06 09:08:35 [error    ] operation_failed                 operation=risky_operation error_type=ValueError error_message="Invalid value"
Traceback (most recent call last):
  File "module.py", line 123, in process
    result = risky_operation()
ValueError: Invalid value
```

---

## Testing

### 10. Testing with Captured Logs

```python
import pytest
from llm_sim.utils.logging import configure_logging, get_logger

def test_logging_context(caplog):
    """Test that context is included in logs."""
    configure_logging(format="json")  # Use JSON for easy parsing

    logger = get_logger(__name__).bind(run_id="test-123")

    with caplog.at_level("INFO"):
        logger.info("test_event", data="value")

    # Verify log record
    record = caplog.records[0]
    assert record.msg == "test_event"
    # Context available in record (exact field depends on structlog config)
```

### 11. Testing Console Output

```python
from io import StringIO
import sys

def test_console_format():
    """Test console output format."""
    # Capture stdout
    captured = StringIO()
    sys.stdout = captured

    configure_logging(format="console")
    logger = get_logger(__name__)
    logger.info("test_event", key="value")

    # Restore stdout
    sys.stdout = sys.__stdout__

    output = captured.getvalue()

    # Verify format
    assert "[info     ]" in output
    assert "test_event" in output
    assert "key=value" in output
```

---

## Migration from Old Logging

### 12. Before (Manual Context Passing)

```python
# OLD: Pass context on every log call
logger = get_logger(__name__)
logger.info("event1", run_id=run_id, simulation=simulation, key="value")
logger.info("event2", run_id=run_id, simulation=simulation, other="data")
logger.info("event3", run_id=run_id, simulation=simulation, more="info")
```

### 13. After (Bound Context)

```python
# NEW: Bind context once, use everywhere
logger = get_logger(__name__).bind(run_id=run_id, simulation=simulation)
logger.info("event1", key="value")
logger.info("event2", other="data")
logger.info("event3", more="info")
```

**Benefits**:
- Less code duplication (DRY principle)
- Impossible to forget context on some calls
- Cleaner, more readable log calls

---

## Production Deployment

### 14. Environment-Based Configuration

```bash
# Development (console with colors)
export ENVIRONMENT=development
python run_simulation.py
# Uses console format with colors

# Production (JSON for log aggregators)
export ENVIRONMENT=production
python run_simulation.py
# Uses JSON format, no colors
```

### 15. JSON Output for Log Aggregation

```python
# Configure for production
configure_logging(level="INFO", format="json")

# Logs output as JSON (one per line)
logger.info("simulation_completed", run_id="demo-123", turns=100, status="success")
```

**Output**:
```json
{"timestamp": "2025-10-06T09:08:33.123456Z", "level": "info", "event": "simulation_completed", "run_id": "demo-123", "turns": 100, "status": "success"}
```

**Works with**:
- Elasticsearch/Logstash/Kibana (ELK stack)
- Grafana Loki
- AWS CloudWatch
- Google Cloud Logging
- Any JSON log aggregator

---

## Best Practices

### ✅ DO

- Use `get_logger(__name__)` for module-level loggers (hierarchical naming)
- Bind context early (in `__init__`) to avoid repetition
- Use descriptive event names (`simulation_starting`, not `start`)
- Include relevant context and data in log calls
- Use appropriate log levels (DEBUG for details, INFO for key events, WARNING for concerns, ERROR for failures)

### ❌ DON'T

- Don't use print() statements - use structured logging
- Don't log sensitive data (passwords, API keys, personal info)
- Don't bind non-JSON-serializable objects (threads, locks, file handles)
- Don't mutate objects and log them (copy first if needed)
- Don't use string formatting in event names - use parameters

---

## Next Steps

1. **Read contracts**: See `contracts/` directory for detailed API contracts
2. **Run tests**: `uv run pytest tests/contract/test_logging_*.py` (will fail initially - TDD red phase)
3. **Implement**: Enhance `utils/logging.py` to make tests pass
4. **Validate**: Run quickstart examples to verify behavior
5. **Deploy**: Configure for production and monitor logs

---

*Quickstart complete - Ready for implementation*
