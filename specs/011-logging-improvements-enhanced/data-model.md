# Data Model: Enhanced Logging

**Feature**: 011-logging-improvements-enhanced
**Date**: 2025-10-06

## Overview

This document defines the data structures and relationships for the enhanced logging system. The model is conceptual - focusing on what data exists and how it relates, not how it's implemented.

## Core Entities

### 1. LogContext

**Description**: A collection of key-value pairs that provide contextual information for log events.

**Attributes**:
- **run_id** (string): Unique identifier for simulation execution
- **simulation_name** (string): Name of the simulation being run
- **component** (string): Name of the component logging the event (e.g., "orchestrator", "agent", "engine")
- **agent_id** (string, optional): Identifier for the agent if log originates from agent
- **turn** (integer, optional): Current simulation turn number
- **request_id** (string, optional): External correlation ID from API or CLI
- **user_id** (string, optional): External user identifier if provided
- **custom_fields** (dict, optional): Any additional context key-value pairs

**Relationships**:
- Bound to → BoundLogger (one-to-one)
- Included in → LogRecord (one-to-many)

**Lifecycle**:
1. Created during logger configuration or binding
2. Persists for lifetime of BoundLogger instance
3. Merged into every LogRecord produced by that logger

**Validation Rules**:
- All values must be JSON-serializable
- Keys must be valid Python identifiers (no spaces, special chars)
- run_id format: "{simulation_name}-{timestamp}"

**Example**:
```
LogContext {
    run_id: "economic-sim-20251006-090833",
    simulation_name: "economic-sim",
    component: "orchestrator",
    request_id: "req-abc-123"
}
```

---

### 2. BoundLogger

**Description**: A logger instance with permanently attached context that is included in all log events.

**Attributes**:
- **name** (string): Hierarchical logger name (e.g., "llm_sim.orchestrator")
- **bound_context** (LogContext): Context permanently attached to this logger
- **level** (string): Minimum log level for this logger ("DEBUG", "INFO", "WARNING", "ERROR")

**Relationships**:
- Has → LogContext (one-to-one)
- Produces → LogRecord (one-to-many)
- Derived from → BoundLogger (zero-to-one, via .bind() call)

**Operations**:
- **bind**(context: dict) → BoundLogger: Create new logger with additional context merged
- **info**(event: string, **kwargs) → None: Log INFO level event
- **debug**(event: string, **kwargs) → None: Log DEBUG level event
- **warning**(event: string, **kwargs) → None: Log WARNING level event
- **error**(event: string, **kwargs) → None: Log ERROR level event

**Immutability**:
- BoundLogger instances are immutable
- `.bind()` returns NEW logger instance with merged context
- Original logger unchanged

**Example**:
```
base_logger = get_logger("llm_sim.orchestrator")
# BoundLogger { name: "llm_sim.orchestrator", bound_context: {} }

bound_logger = base_logger.bind(run_id="demo-123")
# BoundLogger { name: "llm_sim.orchestrator", bound_context: {run_id: "demo-123"} }

further_bound = bound_logger.bind(simulation="economic")
# BoundLogger { name: "llm_sim.orchestrator", bound_context: {run_id: "demo-123", simulation: "economic"} }
```

---

### 3. LogRecord

**Description**: A single log event containing timestamp, severity, message, and complete context.

**Attributes**:
- **timestamp** (datetime): ISO 8601 timestamp of when event occurred
- **level** (string): Severity level ("DEBUG", "INFO", "WARNING", "ERROR")
- **event** (string): Name/description of the event (e.g., "simulation_starting")
- **logger_name** (string): Hierarchical name of logger that produced event
- **bound_context** (dict): Context from BoundLogger
- **event_data** (dict): Additional key-value pairs specific to this event
- **exception_info** (dict, optional): Exception traceback if error occurred

**Relationships**:
- Produced by → BoundLogger (many-to-one)
- Contains → LogContext (many-to-one, embedded as bound_context)

**Lifecycle**:
1. Created when logger method called (e.g., `logger.info(...)`)
2. Processed through configured processors (add timestamp, format, etc.)
3. Rendered to output (console or JSON)
4. Discarded (or persisted to file/aggregator)

**Format Examples**:

**JSON Format (production)**:
```json
{
  "timestamp": "2025-10-06T09:08:33.123456Z",
  "level": "info",
  "event": "simulation_starting",
  "logger": "llm_sim.orchestrator",
  "run_id": "economic-sim-20251006-090833",
  "simulation_name": "economic-sim",
  "component": "orchestrator",
  "request_id": "req-abc-123",
  "num_agents": 5,
  "max_turns": 100
}
```

**Console Format (development)**:
```
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=economic-sim-20251006 simulation_name=economic-sim component=orchestrator request_id=req-abc-123 num_agents=5 max_turns=100
```

---

### 4. LoggingConfiguration

**Description**: Configuration parameters for the logging system.

**Attributes**:
- **level** (string): Global log level ("DEBUG", "INFO", "WARNING", "ERROR")
- **format** (string): Output format ("json", "console", or "auto")
- **initial_context** (dict, optional): Context to bind to root logger
- **color_output** (boolean): Enable/disable color coding (auto-detected if not specified)
- **event_padding** (integer): Character width for event name alignment (default: 35)

**Relationships**:
- Applied to → BoundLogger (one-to-many)
- Configures → OutputRenderer (one-to-one)

**Validation Rules**:
- level must be one of: "DEBUG", "INFO", "WARNING", "ERROR"
- format must be one of: "json", "console", "auto"
- event_padding must be 20-100
- initial_context values must be JSON-serializable

**Example**:
```
LoggingConfiguration {
    level: "INFO",
    format: "console",
    initial_context: {"environment": "development"},
    color_output: true,
    event_padding: 35
}
```

---

## Entity Relationships

```
┌─────────────────────────────┐
│   LoggingConfiguration      │
└─────────┬───────────────────┘
          │ configures
          ▼
┌─────────────────────────────┐       ┌──────────────────┐
│      BoundLogger            │──────▶│   LogContext     │
│  (base logger instance)     │  has  └──────────────────┘
└─────────┬───────────────────┘
          │ .bind(context)
          │ creates new
          ▼
┌─────────────────────────────┐       ┌──────────────────┐
│      BoundLogger            │──────▶│   LogContext     │
│  (with bound context)       │  has  │  (merged)        │
└─────────┬───────────────────┘       └──────────────────┘
          │ produces
          ▼
┌─────────────────────────────┐
│       LogRecord             │
│  (contains all context)     │
└─────────────────────────────┘
```

---

## State Transitions

### BoundLogger Binding Flow

```
[Base Logger] ──bind(context1)──▶ [Logger + context1] ──bind(context2)──▶ [Logger + context1 + context2]
     │                                    │                                          │
     │                                    │                                          │
     ├─ info("event1")                    ├─ info("event2")                          ├─ info("event3")
     │                                    │                                          │
     ▼                                    ▼                                          ▼
[Record: {event: "event1"}]    [Record: {event: "event2",      [Record: {event: "event3",
                                         context1: ...}]                 context1: ..., context2: ...}]
```

### Context Propagation Through Async

```
┌──────────────────────────────────────────────────────────┐
│  Main Async Function                                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  bind_contextvars(run_id="demo-123")               │  │
│  │  logger.info("main_started")  # includes run_id   │  │
│  │                                                     │  │
│  │  await nested_async_function()                     │  │
│  │    │                                                │  │
│  │    └──────────────────────────────────┐            │  │
│  │                                        │            │  │
│  │  ┌─────────────────────────────────────▼──────┐    │  │
│  │  │  Nested Async Function                     │    │  │
│  │  │  (context propagates automatically)        │    │  │
│  │  │  logger.info("nested")  # includes run_id  │    │  │
│  │  └────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Context Binding Patterns

### Pattern 1: Orchestrator Context

```
Orchestrator.__init__():
    1. Receive log_context from external system (e.g., {"request_id": "abc-123"})
    2. Configure logging with external context
    3. Bind orchestrator-specific context (run_id, simulation_name)
    4. Result: All orchestrator logs include external + orchestrator context

Context hierarchy:
    External context (request_id)
    └─▶ Orchestrator context (run_id, simulation_name)
        └─▶ Log events (simulation_starting, turn_completed, etc.)
```

### Pattern 2: Agent Context

```
Agent.__init__(name):
    1. Get module-level logger: get_logger(__name__)  # "llm_sim.infrastructure.patterns.llm_agent"
    2. Bind agent instance context: logger.bind(agent_id=name)
    3. Store as instance variable: self.logger
    4. Result: All agent instance logs include agent_id

Context hierarchy:
    Module context (logger name)
    └─▶ Agent instance context (agent_id)
        └─▶ Log events (decision_started, action_completed, etc.)
```

### Pattern 3: Turn Context

```
Orchestrator._run_turn(state):
    1. Create turn-scoped logger: self.logger.bind(turn=state.turn)
    2. Use for all turn-related logging
    3. Result: All turn logs include run_id + simulation + turn

Context hierarchy:
    Orchestrator context (run_id, simulation_name)
    └─▶ Turn context (turn=N)
        └─▶ Log events (turn_started, agent_actions, turn_completed)
```

---

## Data Validation

### LogContext Validation

```python
def validate_log_context(context: dict) -> None:
    """Validate log context dictionary."""
    for key, value in context.items():
        # Keys must be valid identifiers
        if not key.isidentifier():
            raise ValueError(f"Invalid context key: {key}")

        # Values must be JSON-serializable
        import json
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            raise ValueError(f"Context value for '{key}' is not JSON-serializable")
```

### run_id Format Validation

```python
def validate_run_id(run_id: str) -> None:
    """Validate run_id format."""
    # Expected format: "{name}-{timestamp}"
    # Example: "economic-sim-20251006-090833"

    if not run_id:
        raise ValueError("run_id cannot be empty")

    if len(run_id) > 200:
        raise ValueError("run_id too long (max 200 chars)")

    # Must contain at least one hyphen
    if "-" not in run_id:
        raise ValueError("run_id must contain hyphen separator")
```

---

## Performance Considerations

### Context Binding Overhead

- **Operation**: `logger.bind(key=value)`
- **Cost**: O(1) - creates new dictionary with merged keys
- **Memory**: Shallow copy of context dict (~100 bytes per logger)
- **Frequency**: Once per logger instance creation (not per log call)

### Log Record Creation

- **Operation**: `logger.info("event", **kwargs)`
- **Cost**: ~2-3μs per call (structlog benchmarks)
- **Memory**: One dict per log record (~500 bytes average)
- **Frequency**: ~10-100 per simulation turn

### Estimated Overhead

For typical simulation with 1000 turns, 5 agents:
- Log calls: ~50,000 total
- Overhead: 50,000 × 3μs = 150ms = 0.15 seconds
- **Impact**: <1% of typical simulation runtime

---

## Contract Compliance

This data model supports all functional requirements:

- **FR-001**: LoggingConfiguration supports initial_context parameter ✅
- **FR-002**: configure_logging returns BoundLogger ✅
- **FR-005**: BoundLogger.bind() supports key-value binding ✅
- **FR-006**: Orchestrator binds run_id and simulation_name ✅
- **FR-007**: Agent binds agent_id ✅
- **FR-009**: contextvars processor enables async propagation ✅
- **FR-010-012**: log_context parameter supports external correlation ✅
- **FR-024-026**: LogRecord contains all context fields ✅

---

## Testing Implications

### Unit Tests Required

1. **LogContext validation**: Test valid/invalid keys and values
2. **BoundLogger immutability**: Verify .bind() doesn't mutate original
3. **Context merging**: Test that bind() merges contexts correctly
4. **JSON serialization**: Verify all context values are JSON-serializable

### Contract Tests Required

1. **Logger configuration contract**: Test configure_logging() API
2. **Context binding contract**: Test bind() behavior and context propagation
3. **Console output contract**: Test format and color rendering
4. **JSON output contract**: Test JSON structure and field presence

### Integration Tests Required

1. **End-to-end logging**: External context → orchestrator → agent → logs
2. **Async propagation**: Verify context flows through await calls
3. **Multi-logger**: Test multiple bound loggers don't interfere

---

*Data model complete - Ready for contract generation*
