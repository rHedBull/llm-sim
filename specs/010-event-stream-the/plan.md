# Implementation Plan: Event Stream Activity Logging

**Branch**: `010-event-stream-the` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-event-stream-the/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → SUCCESS: Spec loaded and analyzed
2. Fill Technical Context
   → Project Type: Single (Python simulation framework)
   → Structure Decision: Single project with src/ and tests/
3. Fill Constitution Check section
   → PASS: Event streaming aligns with observability principle
4. Evaluate Constitution Check section
   → No violations detected
   → Update Progress Tracking: Initial Constitution Check ✓
5. Execute Phase 0 → research.md
   → All clarifications resolved in spec
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Generate event data model and API contracts
7. Re-evaluate Constitution Check section
   → PASS: Design maintains simplicity
   → Update Progress Tracking: Post-Design Constitution Check ✓
8. Plan Phase 2 → Task generation approach described
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phase 2 is executed by /tasks command.

## Summary

Event Stream Activity Logging adds fine-grained observability to simulations by capturing every significant action, decision, state transition, and system event between checkpoint snapshots. Events are written to JSONL files with configurable verbosity levels (MILESTONE, DECISION, ACTION, STATE, DETAIL), enabling timeline visualization, causality analysis, and simulation replay. The API server discovers and serves events with filtering by agent, time range, turn number, and event type. File rotation at 500MB ensures manageable file sizes for long-running simulations.

**Technical Approach**: Integrate event emitters at key points in the orchestrator and engine; write events asynchronously to JSONL files with atomic rotation; implement API endpoints for event discovery and filtered retrieval.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (data models), structlog 24.x (logging), httpx (async I/O), FastAPI (API server)
**Storage**: File system (JSONL files in output/{run_id}/events*.jsonl)
**Testing**: pytest with pytest-asyncio for async event writers
**Target Platform**: Linux/macOS servers
**Project Type**: Single project (simulation framework)
**Performance Goals**: Non-blocking event writes; <1ms overhead per event at ACTION level; handle 1000 events/sec
**Constraints**: Drop events under backlog (simulation > observability); 500MB file rotation limit; ISO 8601 timestamps
**Scale/Scope**: 10-100k events per simulation run; 5 verbosity levels; multi-file aggregation in API

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: KISS (Keep It Simple and Stupid)
- ✅ **PASS**: Simple file-based JSONL storage; no complex database
- ✅ **PASS**: Flat event schema with optional fields; no deep nesting
- ✅ **PASS**: Straightforward verbosity filtering; no complex rule engine

### Principle 2: DRY (Don't Repeat Yourself)
- ✅ **PASS**: Single EventWriter class for all event types
- ✅ **PASS**: Centralized verbosity level configuration
- ✅ **PASS**: Reusable event emission helpers across orchestrator/engine

### Principle 3: No Legacy Support
- ✅ **PASS**: New feature; no legacy compatibility needed
- ✅ **PASS**: Single event schema version from start

### Principle 4: Test-First Development
- ✅ **PASS**: Contract tests for event schema before implementation
- ✅ **PASS**: Integration tests for orchestrator event emission before coding
- ✅ **PASS**: API endpoint tests before server implementation

### Principle 5: Clean Interface Design
- ✅ **PASS**: Explicit EventWriter interface with type annotations
- ✅ **PASS**: Typed Event Pydantic models for each event type
- ✅ **PASS**: Clear separation: EventWriter (I/O) vs EventBuilder (construction)

### Principle 6: Observability and Debugging
- ✅ **PASS**: Structured logging for event writer failures
- ✅ **PASS**: Event drop warnings logged with counts
- ✅ **PASS**: Corruption detection on API server startup

### Principle 7: Python Package Management with uv
- ✅ **PASS**: Dependencies added via `uv add fastapi uvicorn`
- ✅ **PASS**: Tests executed with `uv run pytest`
- ✅ **PASS**: pyproject.toml as single source of dependency truth

**Initial Constitution Check**: ✅ PASS (2025-10-04)

## Project Structure

### Documentation (this feature)
```
specs/010-event-stream-the/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── event-schema.json
│   └── api-openapi.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── models/
│   ├── event.py                    # NEW: Event Pydantic models
│   └── event_filter.py             # NEW: Filter criteria models
├── infrastructure/
│   ├── events/
│   │   ├── __init__.py             # NEW: Event infrastructure
│   │   ├── writer.py               # NEW: EventWriter with rotation
│   │   ├── builder.py              # NEW: EventBuilder helpers
│   │   └── config.py               # NEW: Verbosity configuration
│   └── observability/              # EXISTING: May integrate here
├── orchestrator.py                 # MODIFIED: Emit events during turns
├── api/                             # NEW: API server package
│   ├── __init__.py
│   ├── server.py                   # FastAPI application
│   ├── routers/
│   │   └── events.py               # Event endpoints
│   └── services/
│       └── event_service.py        # Event discovery & aggregation

tests/
├── contract/
│   ├── test_event_schema.py        # NEW: Event schema validation
│   └── test_api_contracts.py       # NEW: API contract tests
├── integration/
│   ├── test_orchestrator_events.py # NEW: Orchestrator event emission
│   └── test_event_api.py           # NEW: End-to-end API tests
└── unit/
    ├── test_event_writer.py        # NEW: EventWriter unit tests
    ├── test_event_builder.py       # NEW: EventBuilder unit tests
    └── test_event_filter.py        # NEW: Filter logic tests
```

**Structure Decision**: Single project structure maintained. Event streaming integrates as a new `infrastructure/events/` module and optional `api/` package for serving events. Existing orchestrator and engine classes will be modified to emit events at key lifecycle points. Tests follow existing structure with contract/integration/unit layers.

## Phase 0: Outline & Research

### Research Tasks

1. **JSONL Best Practices for Event Streams**
   - Research: Atomic write patterns for JSONL append operations
   - Research: File rotation strategies (size-based vs time-based)
   - Research: Recovery from partially written lines

2. **FastAPI Event Streaming Patterns**
   - Research: Pagination strategies for large JSONL file aggregation
   - Research: Async file I/O with httpx for reading rotated event files
   - Research: OpenAPI schema for filter query parameters

3. **Python Async Event Writing**
   - Research: asyncio queue-based event buffering
   - Research: Background task patterns for non-blocking writes
   - Research: Graceful shutdown with pending event flush

4. **Event ID Generation**
   - Research: UUID vs ULID vs incremental IDs for event_id uniqueness
   - Research: Causality tracking with event ID references

5. **Timestamp Precision**
   - Research: ISO 8601 format with microsecond precision in Python
   - Research: Monotonic clock vs wall clock for event ordering

**Output**: See research.md for consolidated findings

## Phase 1: Design & Contracts

### Data Model (data-model.md)

**Core Entities**:

1. **Event** (base model)
   - event_id: str (ULID for sortable uniqueness)
   - timestamp: datetime (ISO 8601 with microseconds)
   - turn_number: int
   - event_type: Literal["MILESTONE", "DECISION", "ACTION", "STATE", "DETAIL"]
   - simulation_id: str (run_id)
   - agent_id: Optional[str]
   - caused_by: Optional[List[str]] (event_id array)
   - description: Optional[str]
   - details: Optional[Dict[str, Any]]

2. **MilestoneEvent** (Event)
   - milestone_type: Literal["turn_start", "turn_end", "phase_transition"]

3. **DecisionEvent** (Event)
   - decision_type: str
   - old_value: Optional[Any]
   - new_value: Optional[Any]

4. **ActionEvent** (Event)
   - action_type: str
   - action_payload: Dict[str, Any]

5. **StateEvent** (Event)
   - variable_name: str
   - old_value: Any
   - new_value: Any

6. **DetailEvent** (Event)
   - calculation_type: str
   - intermediate_values: Dict[str, Any]

7. **SystemEvent** (Event)
   - error_type: Optional[str]
   - status: str
   - retry_count: Optional[int]

8. **EventFilter**
   - start_timestamp: Optional[datetime]
   - end_timestamp: Optional[datetime]
   - event_types: Optional[List[str]]
   - agent_ids: Optional[List[str]]
   - turn_start: Optional[int]
   - turn_end: Optional[int]
   - limit: int = 1000
   - offset: int = 0

### API Contracts (contracts/)

**Endpoints**:

1. **GET /simulations/{simulation_id}/events**
   - Query params: EventFilter fields
   - Response: `{ events: List[Event], total: int, has_more: bool }`
   - Pagination via limit/offset

2. **GET /simulations/{simulation_id}/events/{event_id}**
   - Response: Single Event with full details

3. **GET /simulations**
   - Response: `{ simulations: List[{id, name, start_time, event_count}] }`

4. **GET /simulations/{simulation_id}/causality/{event_id}**
   - Response: Causality chain (upstream and downstream events)

### Contract Tests

Generated tests in `tests/contract/`:
- `test_event_schema.py`: Validate all Event subclass schemas
- `test_api_contracts.py`: Validate OpenAPI spec compliance

### Integration Test Scenarios

From user stories:
1. Test simulation emits MILESTONE events at turn boundaries
2. Test agent decision captured as DECISION event
3. Test state transition captured as STATE event
4. Test LLM retry captured as SYSTEM event
5. Test event file rotation at 500MB
6. Test API returns filtered events by agent_id
7. Test API aggregates events across rotated files
8. Test verbosity filtering (ACTION level excludes STATE events)

### Agent File Update

Execute: `.specify/scripts/bash/update-agent-context.sh claude`

This will update `/home/hendrik/coding/llm_sim/llm_sim/CLAUDE.md` with:
- Python 3.12 + Pydantic 2.x + FastAPI (event models, API server)
- File system (JSONL event files in output/ directory)
- Recent change: "010-event-stream-the: Added event streaming infrastructure"

**Output**: data-model.md, contracts/, failing contract tests, quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load task template** from `.specify/templates/tasks-template.md`

2. **Generate contract test tasks** (from contracts/):
   - Task: Write failing test for Event base model schema [P]
   - Task: Write failing tests for all Event subclass schemas [P]
   - Task: Write failing test for EventFilter schema [P]
   - Task: Write failing test for API GET /events endpoint [P]

3. **Generate model implementation tasks**:
   - Task: Implement Event base Pydantic model
   - Task: Implement all Event subclass models (MILESTONE, DECISION, ACTION, STATE, DETAIL, SYSTEM)
   - Task: Implement EventFilter model

4. **Generate infrastructure tasks**:
   - Task: Implement EventWriter with file rotation logic
   - Task: Implement EventBuilder helper functions
   - Task: Implement verbosity level filtering
   - Task: Integrate event emission into Orchestrator.run() method
   - Task: Integrate event emission into BaseEngine.apply_actions()

5. **Generate API tasks**:
   - Task: Implement FastAPI server with CORS middleware
   - Task: Implement EventService for file discovery & aggregation
   - Task: Implement GET /events endpoint with filtering
   - Task: Implement GET /causality endpoint

6. **Generate integration test tasks**:
   - Task: Test orchestrator emits turn boundary events
   - Task: Test agent decision emits DECISION event
   - Task: Test file rotation creates timestamped files
   - Task: Test API endpoint returns filtered events
   - Task: Test verbosity level filtering works end-to-end

**Ordering Strategy**:
- TDD order: Contract tests → Models → Infrastructure → API → Integration tests
- Dependency order: Event models → EventWriter → Orchestrator integration → API server
- Mark [P] for parallelizable tasks (independent test files, model classes)

**Estimated Output**: 30-35 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)
**Phase 5**: Validation (run full test suite, execute quickstart.md, verify event stream correctness)

## Complexity Tracking

*No constitutional violations detected - table empty*

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md generated
- [x] Phase 1: Design complete (/plan command) ✅ data-model.md, contracts/, quickstart.md, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Task generation strategy documented
- [x] Phase 3: Tasks generated (/tasks command) ✅ tasks.md with 47 numbered tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

**Artifacts Generated** (Phase 0-1):
- ✅ research.md (5 research topics, all unknowns resolved)
- ✅ data-model.md (8 entities with full schemas)
- ✅ contracts/event-schema.json (JSON Schema for all event types)
- ✅ contracts/api-openapi.yaml (OpenAPI 3.0 spec with 4 endpoints)
- ✅ quickstart.md (5 test scenarios, end-to-end validation)
- ✅ CLAUDE.md (updated with Python 3.12, FastAPI, JSONL storage)

---
*Based on Constitution v1.3.0 - See `.specify/memory/constitution.md`*
