# Implementation Plan: Enhanced Logging with Context Binding and Correlation Support

**Branch**: `011-logging-improvements-enhanced` | **Date**: 2025-10-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-logging-improvements-enhanced/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ All context clear - existing codebase, structured logging framework
3. Fill the Constitution Check section
   → ✅ Completed - aligns with KISS, DRY, Observability principles
4. Evaluate Constitution Check section
   → ✅ No violations - enhances existing patterns
5. Execute Phase 0 → research.md
   → ✅ Completed - structlog patterns, context binding approaches
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Completed - data models, logging contracts, examples
7. Re-evaluate Constitution Check
   → ✅ No new violations - simple, clean design
8. Plan Phase 2 → Describe task generation approach
   → ✅ Completed - TDD task ordering defined
9. STOP - Ready for /tasks command
   → ✅ Plan complete
```

## Summary
Enhance the existing structlog-based logging system to support context binding, improved console output, and external correlation IDs. This enables better observability for development and production deployments, allowing logs to be traced from API requests through simulation execution.

**Core Enhancement**: Transform logging from simple event recording to contextual, traceable structured logging with automatic context propagation and developer-friendly output formatting.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: structlog 24.x (existing), Python stdlib contextvars
**Storage**: N/A (logging only - outputs to stdout/files)
**Testing**: pytest (existing test infrastructure)
**Target Platform**: Linux/macOS (development and production)
**Project Type**: Single library (llm_sim framework)
**Performance Goals**: <5% logging overhead, <10μs per context bind operation
**Constraints**: Backward compatible with existing logging calls, zero dependencies beyond structlog
**Scale/Scope**: ~15 modules to update, 50+ log call sites

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: KISS (Keep It Simple and Stupid) ✅ PASS
- **Compliance**: Enhances existing simple structlog configuration rather than introducing new logging framework
- **Evidence**: Uses built-in structlog features (context binding, processors) without custom complexity
- **Risk**: None - simplifies logging by making context automatic rather than manual

### Principle 2: DRY (Don't Repeat Yourself) ✅ PASS
- **Compliance**: Eliminates repeated context passing in log calls through bound loggers
- **Evidence**: Instead of `logger.info("event", run_id=run_id, simulation=sim)` repeated everywhere, bind once: `logger.bind(run_id=run_id)`
- **Risk**: None - reduces duplication across codebase

### Principle 3: No Legacy Support ✅ PASS
- **Compliance**: Backward compatible by design - existing log calls continue working unchanged
- **Evidence**: Adding context binding doesn't break existing `logger.info("event")` calls
- **Risk**: None - purely additive enhancement

### Principle 4: Test-First Development ✅ PASS
- **Compliance**: Contract tests will be written first for logging behavior
- **Evidence**: Tests for context binding, format output, correlation ID propagation before implementation
- **Risk**: None - follows TDD cycle

### Principle 5: Clean Interface Design ✅ PASS
- **Compliance**: Explicit API: `configure_logging(bind_context: dict = None) -> BoundLogger`
- **Evidence**: Type-annotated, single responsibility (configure + return logger)
- **Risk**: None - clean, composable interface

### Principle 6: Observability and Debugging ✅ PASS
- **Compliance**: This feature directly enhances observability
- **Evidence**: Improves log context, traceability, and formatting
- **Risk**: None - core purpose is better observability

### Principle 7: Python Package Management with uv ✅ PASS
- **Compliance**: All testing and development use `uv run`
- **Evidence**: Existing project uses uv, no changes to package management
- **Risk**: None - follows existing patterns

**Overall Assessment**: ✅ NO VIOLATIONS - Feature aligns with all constitutional principles

## Project Structure

### Documentation (this feature)
```
specs/011-logging-improvements-enhanced/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── logging_context_contract.md
│   ├── logger_configuration_contract.md
│   └── console_output_contract.md
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── utils/
│   ├── logging.py       # Enhanced with context binding
│   └── __init__.py
├── orchestrator.py      # Updated to use bound logger
├── infrastructure/
│   ├── patterns/
│   │   ├── llm_agent.py     # Bind agent_id to logger
│   │   ├── llm_engine.py    # Bind component to logger
│   │   └── llm_validator.py # Bind component to logger
│   ├── events/
│   │   └── writer.py        # Standardize logger acquisition
│   └── lifecycle/
│       └── manager.py       # Standardize logger acquisition

tests/
├── contract/
│   ├── test_logging_context_binding.py
│   ├── test_logger_configuration.py
│   └── test_console_output_format.py
├── integration/
│   └── test_end_to_end_logging.py
└── unit/
    └── test_logging_utils.py
```

**Structure Decision**: Single project structure - all enhancements within existing `src/llm_sim/` hierarchy. Tests follow existing contract/integration/unit organization.

## Phase 0: Outline & Research

### Research Tasks Executed:

1. **structlog Context Binding Patterns**
   - Researched: `BoundLogger.bind()` API and contextvars integration
   - Decision: Use `contextvars.merge_contextvars` processor for async propagation
   - Rationale: Native structlog support, zero custom code needed

2. **Console Output Enhancement**
   - Researched: `ConsoleRenderer` options for colors, alignment, formatting
   - Decision: Use `structlog.dev.ConsoleRenderer(colors=True, pad_event=35)`
   - Rationale: Built-in structlog feature, handles TTY detection automatically

3. **External Context Injection**
   - Researched: Patterns for passing context from parent process to subprocess
   - Decision: Accept `log_context: dict` parameter in orchestrator initialization
   - Rationale: Simple, explicit, works with any external system

4. **Logger Instance Management**
   - Researched: Singleton vs instance loggers, bound logger lifecycle
   - Decision: Module-level `get_logger(__name__)` + instance binding
   - Rationale: Standard Python logging pattern, hierarchical naming

**Output**: See [research.md](./research.md) for detailed findings

## Phase 1: Design & Contracts

### Data Model (from data-model.md)

**Core Entities**:
1. **LogContext** - Dict of key-value pairs for binding to loggers
2. **BoundLogger** - structlog logger with persistent context
3. **LogRecord** - Emitted log event with timestamp, level, event, context

### API Contracts (from contracts/)

**Contract 1: Logger Configuration** (`contracts/logger_configuration_contract.md`)
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
        Configured logger with bound context
    """
```

**Contract 2: Context Binding** (`contracts/logging_context_contract.md`)
```python
# Orchestrator binds run_id and simulation_name
logger = configure_logging().bind(
    run_id="demo-20251006-090833",
    simulation_name="economic-simulation"
)

# All subsequent logs include context automatically
logger.info("simulation_starting")  # includes run_id + simulation_name

# Agent binds agent_id to instance logger
self.logger = get_logger(__name__).bind(agent_id=self.name)
```

**Contract 3: Console Output** (`contracts/console_output_contract.md`)
```
Expected console format (development mode):
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-20251006 simulation_name=economic num_agents=5
2025-10-06 09:08:33 [info     ] turn_started                     run_id=demo-20251006 turn=1 active_agents=5 paused_agents=0
2025-10-06 09:08:34 [info     ] agent_decision_started           run_id=demo-20251006 agent_id=agent_alpha turn=1
```

### Contract Tests (must fail initially)

See `tests/contract/test_logging_*.py` files generated in Phase 1.

### Quickstart Guide

See [quickstart.md](./quickstart.md) for developer workflow examples.

### Agent File Update

CLAUDE.md will be updated with:
- New technologies: contextvars, structlog context binding patterns
- Recent changes: Enhanced logging with bound context (feature 011)
- Code style: Use `get_logger(__name__)` for all modules

**Output**: data-model.md, contracts/, failing contract tests, quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 contracts and data model
3. Each contract → contract test task [P]
4. Each module to update → update task (after tests)
5. Integration tests for end-to-end logging flow

**Ordering Strategy** (TDD):
1. **Contract Test Tasks** [P] - Can run in parallel, all fail initially
   - Test logging configuration contract
   - Test context binding contract
   - Test console output format contract

2. **Implementation Tasks** - Sequential, make tests pass
   - Enhance `utils/logging.py` with context binding
   - Update `orchestrator.py` to use bound logger
   - Update agent classes to bind agent_id
   - Update infrastructure components to bind component name
   - Standardize logger acquisition across all modules

3. **Integration Test Tasks**
   - End-to-end test: API → orchestrator → logs with correlation ID
   - Multi-simulation test: Verify log filtering by run_id

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md

**Dependencies**:
- Contract tests (1-3) have no dependencies [P]
- Implementation tasks depend on contract tests existing
- Integration tests depend on implementation complete

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD cycle)
**Phase 5**: Validation (run tests, execute quickstart.md, verify console/JSON output)

## Complexity Tracking
*No constitutional violations - this section is empty*

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (none existed)
- [x] Complexity deviations documented (none)

---
*Based on Constitution v1.3.0 - See `.specify/memory/constitution.md`*
