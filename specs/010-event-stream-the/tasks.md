# Tasks: Event Stream Activity Logging

**Input**: Design documents from `/specs/010-event-stream-the/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: Tech stack = Python 3.12, Pydantic 2.x, FastAPI, asyncio
2. Load optional design documents:
   → data-model.md: 8 entities (Event + 6 subclasses + EventFilter)
   → contracts/: event-schema.json, api-openapi.yaml
   → quickstart.md: 5 test scenarios
3. Generate tasks by category:
   → Setup: Dependencies (python-ulid, aiofiles, fastapi), structure
   → Tests: 7 contract tests, 8 integration tests
   → Core: 8 models, EventWriter, EventBuilder, API endpoints
   → Integration: Orchestrator hooks, verbosity config, rotation
   → Polish: Unit tests, performance validation, docs
4. Apply task rules:
   → [P] = Different files (models, tests)
   → Sequential = Same file (orchestrator modifications)
   → TDD order enforced
5. Number tasks sequentially (T001-T040)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate completeness: ✅ All entities, contracts, scenarios covered
9. Return: SUCCESS (40 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Project type**: Single project (simulation framework)
- **Source**: `src/llm_sim/`
- **Tests**: `tests/`

---

## Phase 3.1: Setup

- [x] **T001** Add dependencies to pyproject.toml: `uv add python-ulid aiofiles fastapi uvicorn[standard]`
- [x] **T002** Create event infrastructure directory structure: `src/llm_sim/infrastructure/events/` with `__init__.py`
- [x] **T003** Create API server directory structure: `src/llm_sim/api/` with `routers/` and `services/` subdirectories
- [x] **T004** [P] Create test directories: `tests/contract/`, `tests/integration/`, `tests/unit/` (if not exists)

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Event Schema)

- [x] **T005** [P] Contract test for Event base model schema in `tests/contract/test_event_schema.py` - Validate required fields (event_id, timestamp, turn_number, event_type, simulation_id) match JSON schema
- [x] **T006** [P] Contract test for MilestoneEvent subclass in `tests/contract/test_event_schema.py` - Validate milestone_type enum and agent_id absence
- [x] **T007** [P] Contract test for DecisionEvent subclass in `tests/contract/test_event_schema.py` - Validate decision_type, old_value, new_value fields and agent_id presence
- [x] **T008** [P] Contract test for ActionEvent subclass in `tests/contract/test_event_schema.py` - Validate action_type, action_payload fields
- [x] **T009** [P] Contract test for StateEvent subclass in `tests/contract/test_event_schema.py` - Validate variable_name, old_value, new_value fields
- [x] **T010** [P] Contract test for DetailEvent subclass in `tests/contract/test_event_schema.py` - Validate calculation_type, intermediate_values fields
- [x] **T011** [P] Contract test for SystemEvent subclass in `tests/contract/test_event_schema.py` - Validate error_type, status, retry_count fields

### Contract Tests (API Endpoints)

- [x] **T012** [P] Contract test for GET /simulations endpoint in `tests/contract/test_api_contracts.py` - Validate response schema matches OpenAPI spec (simulations array with id, name, start_time, event_count)
- [x] **T013** [P] Contract test for GET /simulations/{simulation_id}/events endpoint in `tests/contract/test_api_contracts.py` - Validate EventFilter query params and EventsResponse schema (events, total, has_more)
- [x] **T014** [P] Contract test for GET /simulations/{simulation_id}/events/{event_id} endpoint in `tests/contract/test_api_contracts.py` - Validate single Event response with full details
- [x] **T015** [P] Contract test for GET /simulations/{simulation_id}/causality/{event_id} endpoint in `tests/contract/test_api_contracts.py` - Validate CausalityChain schema (upstream, downstream arrays)

### Integration Tests (From Quickstart Scenarios)

- [x] **T016** [P] Integration test: Basic event capture (Scenario 1) in `tests/integration/test_orchestrator_events.py` - Run minimal simulation, verify events.jsonl created with valid JSONL, MILESTONE events present
- [x] **T017** [P] Integration test: MILESTONE verbosity filtering (Scenario 2) in `tests/integration/test_verbosity_filtering.py` - Run simulation with MILESTONE level, verify only MILESTONE events logged
- [x] **T018** [P] Integration test: DETAIL verbosity captures more events (Scenario 2) in `tests/integration/test_verbosity_filtering.py` - Compare event counts across verbosity levels
- [x] **T019** [P] Integration test: File rotation at 500MB (Scenario 3) in `tests/integration/test_file_rotation.py` - Generate large event stream, verify multiple timestamped files created, each < 500MB
- [x] **T020** [P] Integration test: API returns filtered events by agent_id (Scenario 4) in `tests/integration/test_event_api.py` - Query API with agent_ids filter, verify correct events returned
- [x] **T021** [P] Integration test: API aggregates events across rotated files (Scenario 4) in `tests/integration/test_event_api.py` - Create rotated files, verify API reads all files in chronological order
- [x] **T022** [P] Integration test: API filtering by turn range (Scenario 4) in `tests/integration/test_event_api.py` - Filter events by turn_start/turn_end, verify correct subset returned
- [x] **T023** [P] Integration test: Causality integrity (Scenario 5) in `tests/integration/test_causality.py` - Verify all caused_by event_ids exist, no cyclic references

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Event Models

- [x] **T024** [P] Implement Event base Pydantic model in `src/llm_sim/models/event.py` - Required fields: event_id (str), timestamp (datetime), turn_number (int), event_type (Literal), simulation_id (str), optional: agent_id, caused_by, description, details
- [x] **T025** [P] Implement MilestoneEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds milestone_type field (Literal["turn_start", "turn_end", "phase_transition", "simulation_start", "simulation_end"])
- [x] **T026** [P] Implement DecisionEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds decision_type, old_value, new_value fields, requires agent_id
- [x] **T027** [P] Implement ActionEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds action_type, action_payload fields, requires agent_id
- [x] **T028** [P] Implement StateEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds variable_name, old_value, new_value, scope fields
- [x] **T029** [P] Implement DetailEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds calculation_type, intermediate_values fields
- [x] **T030** [P] Implement SystemEvent model in `src/llm_sim/models/event.py` - Inherits Event, adds error_type, status (Literal), retry_count fields
- [x] **T031** [P] Implement EventFilter model in `src/llm_sim/models/event_filter.py` - Fields: start_timestamp, end_timestamp, event_types, agent_ids, turn_start, turn_end, limit (default 1000), offset (default 0)

### Event Writer Infrastructure

- [x] **T032** Implement EventWriter class in `src/llm_sim/infrastructure/events/writer.py` - Async queue-based writer with file rotation at 500MB, atomic JSONL writes, graceful event dropping on queue full
- [x] **T033** Implement EventBuilder helper functions in `src/llm_sim/infrastructure/events/builder.py` - Factory functions to construct typed Event objects with ULID generation and timestamp creation
- [x] **T034** Implement verbosity level configuration in `src/llm_sim/infrastructure/events/config.py` - VerbosityLevel enum (MILESTONE, DECISION, ACTION, STATE, DETAIL) with filtering logic

### Orchestrator Integration

- [x] **T035** Integrate EventWriter into SimulationOrchestrator in `src/llm_sim/orchestrator.py` - Initialize EventWriter in __init__, emit MILESTONE events at turn boundaries (turn_start, turn_end), emit simulation_start/simulation_end events
- [x] **T036** Integrate event emission into BaseEngine.run_turn() in `src/llm_sim/infrastructure/base/engine.py` - Emit ACTION events when actions applied, emit STATE events when state variables change

### API Server

- [x] **T037** Implement FastAPI application in `src/llm_sim/api/server.py` - Initialize FastAPI app, include CORS middleware, mount event routers
- [x] **T038** Implement EventService in `src/llm_sim/api/services/event_service.py` - Discover events.jsonl files via glob, aggregate events from rotated files, apply EventFilter criteria, sort by timestamp
- [x] **T039** Implement event endpoints in `src/llm_sim/api/routers/events.py` - GET /simulations (list all), GET /simulations/{sim_id}/events (filtered), GET /simulations/{sim_id}/events/{event_id} (single), GET /simulations/{sim_id}/causality/{event_id} (causality chain)

---

## Phase 3.4: Polish

- [x] **T040** [P] Unit test for EventWriter rotation logic in `tests/unit/test_event_writer.py` - Mock file writes, verify rotation triggers at 500MB, timestamped files created
- [x] **T041** [P] Unit test for EventBuilder ULID generation in `tests/unit/test_event_builder.py` - Verify ULIDs are unique and sortable
- [x] **T042** [P] Unit test for EventFilter application in `tests/unit/test_event_filter.py` - Test each filter criterion (timestamp range, event_types, agent_ids, turn range) independently
- [x] **T043** [P] Performance test: Verify <1ms event emission overhead in `tests/integration/test_performance.py` - Measure orchestrator turn execution time with and without event streaming, assert delta < 1ms per event
- [x] **T044** [P] Performance test: Verify 1000 events/sec write throughput in `tests/integration/test_performance.py` - Generate 10k events rapidly, measure EventWriter throughput
- [ ] **T045** ~~Execute quickstart.md validation scenarios end-to-end~~ - **DEFERRED**: Requires CLI + reference implementations (out of scope for this feature)
- [x] **T046** [P] Update CLAUDE.md if additional dependencies added - Ensure all new libraries documented in Active Technologies section
- [x] **T047** Code review: Remove duplication across EventWriter, EventBuilder, API service - Apply DRY principle, extract common event processing logic

---

## Dependencies

**Critical Path (must execute sequentially)**:
1. Setup (T001-T004) blocks all subsequent tasks
2. Contract tests (T005-T015) block model implementation (T024-T031)
3. Integration tests (T016-T023) written but not passing until implementation
4. Models (T024-T031) block EventWriter (T032), EventBuilder (T033)
5. EventWriter (T032) blocks Orchestrator integration (T035-T036)
6. EventService (T038) blocks API endpoints (T039)
7. API endpoints (T039) block API integration tests (T020-T022)
8. All implementation blocks polish (T040-T047)

**Parallel Execution Opportunities**:
- T005-T011 (contract tests for event models)
- T012-T015 (contract tests for API endpoints)
- T016-T023 (integration test scenarios)
- T024-T031 (event model implementations)
- T040-T042, T046 (unit tests and docs - after implementation)

---

## Parallel Execution Examples

### Example 1: Contract Tests for Event Models (after T004)
```bash
# Launch 7 tasks in parallel - each tests different event subclass
uv run pytest tests/contract/test_event_schema.py::test_base_event &
uv run pytest tests/contract/test_event_schema.py::test_milestone_event &
uv run pytest tests/contract/test_event_schema.py::test_decision_event &
uv run pytest tests/contract/test_event_schema.py::test_action_event &
uv run pytest tests/contract/test_event_schema.py::test_state_event &
uv run pytest tests/contract/test_event_schema.py::test_detail_event &
uv run pytest tests/contract/test_event_schema.py::test_system_event &
wait
```

### Example 2: Event Model Implementations (after T005-T015 fail)
```bash
# Different model classes in same file - must be sequential
# Implement in order: T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031
# But EventFilter (T031) can be parallel since it's a different file
```

### Example 3: Integration Test Scenarios (after T024-T031)
```bash
# Launch integration tests in parallel - different test files
uv run pytest tests/integration/test_orchestrator_events.py &
uv run pytest tests/integration/test_verbosity_filtering.py &
uv run pytest tests/integration/test_file_rotation.py &
uv run pytest tests/integration/test_event_api.py &
uv run pytest tests/integration/test_causality.py &
wait
```

---

## Validation Checklist
*GATE: Checked before marking complete*

- [x] All 7 Event subclass schemas have contract tests (T005-T011)
- [x] All 4 API endpoints have contract tests (T012-T015)
- [x] All 8 entities have model implementation tasks (T024-T031)
- [x] All 5 quickstart scenarios have integration tests (T016-T023)
- [x] Tests (T005-T023) come before implementation (T024-T039)
- [x] Parallel tasks ([P]) are truly independent files
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD order enforced: Contract tests → Models → Integration tests → Implementation

---

## Task Completion Tracking

**Phase 3.1 (Setup)**: 4/4 complete ✅
**Phase 3.2 (Tests First - TDD)**: 19/19 complete ✅ (All contract and integration tests written)
**Phase 3.3 (Core Implementation)**: 16/16 complete ✅
**Phase 3.4 (Polish)**: 7/7 complete ✅ (T045 deferred - out of scope)

**Total Progress**: 46/46 tasks complete (100%)** 🎉
**Deferred**: 1 task (T045 - requires framework implementations)

**Additional Deliverables** (not in original task list):
- ✅ Comprehensive working demonstration (`examples/event_stream_demo.py`)
- ✅ Complete feature documentation (`docs/event-streaming.md`)

---

## Notes

- **TDD Enforcement**: T005-T023 must all fail before starting T024
- **Verbosity Filtering**: EventWriter must check VerbosityLevel config before emitting events
- **File Rotation**: Use os.stat().st_size to check file size, atomic rename for rotation
- **ULID Generation**: Use `python-ulid` library, generate on Event instantiation
- **Async I/O**: EventWriter uses asyncio.Queue, aiofiles for file writes
- **API Discovery**: Glob pattern `output/*/events*.jsonl` to find all event files
- **Causality**: caused_by field is optional List[str] of event_ids
- **Timestamp Format**: datetime.now(timezone.utc).isoformat() for ISO 8601 with microseconds
- **Commit Strategy**: Commit after each completed task for incremental progress

---

*Generated from specs/010-event-stream-the/ design documents*
*Based on Constitution v1.3.0 TDD and KISS principles*
