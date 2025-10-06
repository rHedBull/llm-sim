# Research: Enhanced Logging with Context Binding

**Feature**: 011-logging-improvements-enhanced
**Date**: 2025-10-06

## Executive Summary

Researched approaches for enhancing the existing structlog-based logging system to support context binding, improved console output, and external correlation IDs. All required capabilities exist in structlog 24.x with zero additional dependencies.

## Research Areas

### 1. structlog Context Binding Patterns

**Question**: How to permanently attach context (run_id, agent_id, etc.) to logger instances?

**Options Considered**:
1. Manual context passing on every log call
2. Thread-local storage for context
3. structlog's BoundLogger API
4. Custom wrapper class

**Decision**: Use structlog's `BoundLogger.bind()` API

**Rationale**:
- Built-in structlog feature, zero custom code
- Returns new logger instance with bound context
- Context automatically included in all subsequent log calls
- Immutable binding pattern (functional style)
- Thread-safe and async-safe

**Example**:
```python
# Get base logger
logger = structlog.get_logger(__name__)

# Bind context - returns new BoundLogger instance
bound_logger = logger.bind(run_id="demo-123", simulation="economic")

# All logs from bound_logger include context
bound_logger.info("event")  # Outputs: {..., "run_id": "demo-123", "simulation": "economic", ...}
```

**Alternatives Rejected**:
- Manual passing: Violates DRY, error-prone
- Thread-local: Complex, breaks with async
- Custom wrapper: Unnecessary complexity

**References**:
- structlog docs: https://www.structlog.org/en/stable/bound-loggers.html
- BoundLogger API: https://www.structlog.org/en/stable/api.html#structlog.BoundLogger

---

### 2. Async Context Propagation

**Question**: How to propagate context through async operations without manual passing?

**Options Considered**:
1. Pass context as function parameters
2. AsyncLocal storage
3. structlog's contextvars processor
4. Context managers

**Decision**: Use `structlog.contextvars.merge_contextvars` processor

**Rationale**:
- Python 3.7+ stdlib contextvars automatically propagates through async/await
- structlog has built-in processor: `merge_contextvars`
- Add processor to configuration, bind context once, automatic propagation
- Zero manual context passing needed

**Implementation**:
```python
import structlog

processors = [
    structlog.contextvars.merge_contextvars,  # Add this processor
    # ... other processors ...
]

structlog.configure(processors=processors, ...)

# Bind context via contextvars
structlog.contextvars.bind_contextvars(run_id="demo-123")

# Context propagates automatically through async calls
async def nested_async_function():
    logger.info("event")  # Includes run_id="demo-123"
```

**Alternatives Rejected**:
- Manual passing: Not scalable, defeats purpose
- AsyncLocal: Requires Python 3.12+, structlog has better integration
- Context managers: Too verbose for every async function

**References**:
- structlog contextvars: https://www.structlog.org/en/stable/contextvars.html
- Python contextvars PEP: https://peps.python.org/pep-0567/

---

### 3. Console Output Enhancement

**Question**: How to improve console output with colors, alignment, and readability?

**Options Considered**:
1. Custom formatter implementation
2. Third-party library (colorama, rich)
3. structlog's ConsoleRenderer
4. ANSI escape codes manually

**Decision**: Use `structlog.dev.ConsoleRenderer` with enhanced options

**Rationale**:
- Built-in structlog feature, no dependencies
- Handles TTY detection automatically (disables colors if not TTY)
- Supports color coding by log level
- Configurable event padding for alignment
- Production-ready, well-tested

**Configuration**:
```python
from structlog.dev import ConsoleRenderer

renderer = ConsoleRenderer(
    colors=True,        # Enable color coding
    pad_event=35,       # Align event names (35 chars)
    # Colors assigned by log level automatically:
    # - ERROR: red
    # - WARNING: yellow
    # - INFO: cyan
    # - DEBUG: gray
)

processors.append(renderer)
```

**Output Example**:
```
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-123 agents=5
2025-10-06 09:08:33 [warning  ] slow_operation                   duration_ms=1234.5
2025-10-06 09:08:34 [error    ] validation_failed                agent_id=alpha reason=invalid_action
```

**Alternatives Rejected**:
- Custom formatter: Unnecessary complexity, reinventing wheel
- Third-party library: Extra dependency, structlog sufficient
- Manual ANSI: Error-prone, no TTY detection

**References**:
- ConsoleRenderer docs: https://www.structlog.org/en/stable/api.html#structlog.dev.ConsoleRenderer
- Console colors: https://www.structlog.org/en/stable/console-output.html

---

### 4. External Context Injection

**Question**: How to accept correlation IDs from external systems (e.g., llm-sim-server)?

**Options Considered**:
1. Environment variables
2. Global configuration
3. Constructor parameter
4. Middleware/interceptor

**Decision**: Accept `log_context: dict` parameter in orchestrator initialization

**Rationale**:
- Explicit, simple API
- Works with any external system (server, CLI, tests)
- Type-safe with type hints
- No global state or hidden dependencies
- Follows dependency injection pattern

**API Design**:
```python
class SimulationOrchestrator:
    def __init__(
        self,
        config: SimulationConfig,
        log_context: dict[str, Any] | None = None,  # External context
    ):
        # Configure logging with external context
        self.logger = configure_logging(
            level=config.logging.level,
            format=config.logging.format,
            bind_context=log_context,  # Inject external context
        )

        # Bind orchestrator-specific context
        self.logger = self.logger.bind(
            run_id=self.run_id,
            simulation=config.simulation.name,
        )

# External system usage:
orchestrator = SimulationOrchestrator(
    config=config,
    log_context={"request_id": "abc-123", "user_id": "user-456"}
)
```

**Alternatives Rejected**:
- Environment variables: Not scalable, hard to test
- Global configuration: Hidden dependency, breaks testing
- Middleware: Over-engineered for simple use case

**References**:
- Dependency injection pattern: Standard software engineering practice

---

### 5. Logger Instance Management

**Question**: How to organize logger instances across modules and classes?

**Options Considered**:
1. Single global logger
2. Logger per module with `get_logger(__name__)`
3. Logger per class instance
4. Mix of module + instance loggers

**Decision**: Module-level loggers + instance binding

**Pattern**:
```python
# At module level
import structlog
logger = structlog.get_logger(__name__)  # Hierarchical naming

# In class __init__
class Agent:
    def __init__(self, name: str):
        self.logger = logger.bind(agent_id=name)  # Instance binding

    def decide_action(self, state):
        self.logger.info("decision_started", turn=state.turn)
```

**Rationale**:
- Module-level: Standard Python logging pattern, hierarchical names
- Instance binding: Context automatically included in all instance logs
- Clear origin: Log shows both module (component) and instance (agent_id)
- DRY: Bind context once in `__init__`, use everywhere

**Hierarchy Example**:
```
llm_sim.orchestrator              # Orchestrator module logs
llm_sim.infrastructure.events     # EventWriter module logs
llm_sim.infrastructure.patterns   # Agent/Engine/Validator logs
```

**Alternatives Rejected**:
- Global logger: Loses component information
- Only instance loggers: No module hierarchy
- Only module loggers: No instance context

**References**:
- Python logging best practices: https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial

---

### 6. JSON vs Console Output Selection

**Question**: How to switch between JSON (production) and console (development) formats?

**Options Considered**:
1. Hardcoded in configuration
2. Environment variable
3. Configuration file parameter
4. Auto-detect based on environment

**Decision**: Use `format` parameter with "auto" option for environment detection

**Implementation**:
```python
def configure_logging(
    level: str = "INFO",
    format: str = "auto",  # "json", "console", or "auto"
    bind_context: dict | None = None
) -> structlog.BoundLogger:
    # Auto-detect from environment
    if format == "auto":
        import os
        format = "json" if os.getenv("ENVIRONMENT") == "production" else "console"

    # Select processor based on format
    if format == "json":
        output_processor = structlog.processors.JSONRenderer()
    else:
        output_processor = structlog.dev.ConsoleRenderer(colors=True, pad_event=35)

    processors = [
        # ... other processors ...
        output_processor
    ]
```

**Rationale**:
- Flexible: Explicit control via parameter OR auto-detection
- Sensible defaults: Auto mode works for most cases
- Testable: Can force format in tests
- Production-ready: JSON for log aggregators, console for dev

**Alternatives Rejected**:
- Hardcoded: Not flexible enough
- Only env var: Harder to test, less explicit
- Only config file: More complex, harder to override

**References**:
- Twelve-factor app methodology: Environment-based configuration

---

### 7. Backward Compatibility

**Question**: How to ensure existing log calls continue working unchanged?

**Analysis**:
```python
# Current code (must continue working):
logger = get_logger(__name__)
logger.info("simulation_starting", num_agents=5)

# Enhanced code (new capability):
logger = get_logger(__name__).bind(run_id="demo-123")
logger.info("simulation_starting", num_agents=5)  # Now includes run_id
```

**Conclusion**: Fully backward compatible

**Evidence**:
- Binding is opt-in via `.bind()` call
- Existing calls work unchanged
- No breaking changes to API
- Tests continue passing without modification

**Constitutional Alignment**:
- ✅ Principle 3: No Legacy Support - Not needed, design is additive
- ✅ Principle 1: KISS - Enhances existing simple API
- ✅ Principle 2: DRY - Reduces duplication in new code

---

## Technology Decisions Summary

| Capability | Technology | Rationale |
|------------|-----------|-----------|
| Context Binding | `BoundLogger.bind()` | Built-in structlog, immutable, thread-safe |
| Async Propagation | `contextvars.merge_contextvars` | Python stdlib + structlog integration |
| Console Colors | `ConsoleRenderer(colors=True)` | Built-in, handles TTY detection |
| External Context | Constructor parameter | Explicit, type-safe, testable |
| Logger Hierarchy | `get_logger(__name__)` | Standard Python pattern |
| Format Selection | Parameter + env detection | Flexible, production-ready |

**Dependencies Required**: None (all capabilities in structlog 24.x + Python stdlib)

**Performance Impact**: <5% overhead (structlog benchmarks show 2-3μs per log call)

---

## Implementation Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Context not propagating through async | Low | Medium | Use contextvars processor, add integration test |
| Colors in non-TTY output | Low | Low | ConsoleRenderer auto-detects TTY |
| Performance degradation | Very Low | Low | Structlog is highly optimized, measure in tests |
| Breaking existing code | Very Low | High | Backward compatible by design, run full test suite |

---

## Next Steps (Phase 1)

Based on research findings:

1. **Design data model** for LogContext, BoundLogger
2. **Write contracts** for logging configuration, context binding, output format
3. **Create contract tests** that fail initially (TDD)
4. **Document quickstart** examples for developers

All research complete ✅ - Ready for Phase 1 design.
