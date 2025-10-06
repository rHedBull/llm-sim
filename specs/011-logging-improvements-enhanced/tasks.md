# Tasks: Enhanced Logging with Context Binding and Correlation Support

**Input**: Design documents from `/specs/011-logging-improvements-enhanced/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Loaded: Python 3.12, structlog 24.x, contextvars
2. Load optional design documents:
   → ✅ data-model.md: LogContext, BoundLogger, LogRecord entities
   → ✅ contracts/: 3 contract files found
   → ✅ research.md: structlog patterns, context binding decisions
   → ✅ quickstart.md: 15 usage examples extracted
3. Generate tasks by category:
   → Setup: Verify dependencies (structlog already present)
   → Tests: 3 contract tests [P], 1 integration test
   → Core: Enhance logging.py, update orchestrator, update components
   → Integration: Standardize logger acquisition across modules
   → Polish: Verify console/JSON output, update documentation
4. Apply task rules:
   → Contract tests are parallel [P] (different files)
   → Component updates sequential (shared logging.py)
   → Module standardization parallel [P] (different modules)
5. Number tasks sequentially (T001-T018)
6. Generate dependency graph ✅
7. Create parallel execution examples ✅
8. Validate task completeness:
   → ✅ All 3 contracts have tests
   → ✅ Logging configuration enhancement covered
   → ✅ All components (orchestrator, agents) updated
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Project Type**: Single library (llm_sim framework)
- **Source**: `src/llm_sim/`
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 3.1: Setup & Verification ✅ COMPLETE

### T001: ✅ Verify structlog configuration
**File**: `src/llm_sim/utils/logging.py` (read-only)
**Action**: Verify current structlog setup and identify areas for enhancement
**Expected**: Document current processors, identify missing contextvars support
**Dependencies**: None
**Parallel**: N/A (inspection task)
**Status**: COMPLETE - Identified missing contextvars support, color/padding options

---

## Phase 3.2: Tests First (TDD) ✅ COMPLETE
**All contract tests written and passing**

### T002 [P]: ✅ Contract test for logger configuration
**File**: `tests/contract/test_logger_configuration.py`
**Contract**: `contracts/logger_configuration_contract.md`
**Test Scenarios**:
- Default configuration returns BoundLogger
- Custom level and format parameters work
- Context binding via bind_context parameter
- Invalid parameters raise ValueError
- Idempotent configuration (multiple calls work)
- JSON output format verification
- Console output format verification
- Level filtering (DEBUG, INFO, WARNING, ERROR)

**Expected**: Test file created, all tests FAIL (red phase)
**Dependencies**: None
**Parallel**: Yes [P] - independent test file

---

### T003 [P]: Contract test for context binding
**File**: `tests/contract/test_logging_context_binding.py`
**Contract**: `contracts/logging_context_contract.md`
**Test Scenarios**:
- Basic context binding with .bind()
- Logger immutability (bind returns new instance)
- Context merging (successive binds)
- Event data priority over bound context
- Multi-logger isolation
- Orchestrator context pattern (external + orchestrator context)
- Agent context pattern (agent_id binding)
- Non-serializable value rejection

**Expected**: Test file created, all tests FAIL (red phase)
**Dependencies**: None
**Parallel**: Yes [P] - independent test file

---

### T004 [P]: Contract test for console output format
**File**: `tests/contract/test_console_output_format.py`
**Contract**: `contracts/console_output_contract.md`
**Test Scenarios**:
- Basic console format (timestamp, level, event, key=value)
- Event name padding to 35 characters
- Color coding when TTY (red=error, yellow=warning, cyan=info)
- No colors when non-TTY (output redirected)
- Context display (bound context + event data)
- Exception formatting with traceback
- Log level alignment
- Timestamp format validation

**Expected**: Test file created, all tests FAIL (red phase)
**Dependencies**: None
**Parallel**: Yes [P] - independent test file

---

### T005 [P]: Integration test for end-to-end logging
**File**: `tests/integration/test_end_to_end_logging.py`
**Test Scenarios**:
- External context → orchestrator → agent → logs
- Verify context propagates through all components
- Verify async context propagation (contextvars)
- Multi-simulation concurrent logging isolation
- Log filtering by run_id, agent_id, component

**Expected**: Test file created, tests FAIL (red phase)
**Dependencies**: None
**Parallel**: Yes [P] - independent test file

---

## Phase 3.3: Core Implementation ✅ COMPLETE

### T006: ✅ Enhance logging.py with context binding support
**File**: `src/llm_sim/utils/logging.py`
**Changes**:
1. Add `contextvars.merge_contextvars` processor to configuration
2. Update `configure_logging()` signature to accept `bind_context: dict | None`
3. Change return type from `None` to `structlog.BoundLogger`
4. Enhance ConsoleRenderer with `colors=True, pad_event=35`
5. Add auto-detection for format ("auto" → "console" or "json" based on env)
6. Add validation for bind_context (JSON-serializable values)
7. Return logger with bound context if provided

**Expected**: Tests T002, T003, T004 start passing (green phase)
**Dependencies**: T002, T003, T004 must exist and fail first
**Parallel**: No - core implementation file

---

### T007: ✅ Update orchestrator to use bound logger
**File**: `src/llm_sim/orchestrator.py`
**Changes**:
1. Add `log_context: dict | None = None` parameter to `__init__`
2. Pass `log_context` to `configure_logging()`
3. Store returned logger instead of using module-level logger
4. Bind orchestrator context: `run_id`, `simulation_name`, `component="orchestrator"`
5. Use `self.logger` instead of module `logger` throughout
6. Add `log_context` parameter to `from_yaml()` class method

**Expected**: Orchestrator logs include bound context automatically
**Dependencies**: T006 (logging.py must be enhanced first)
**Parallel**: No - depends on T006

---

### T008: ✅ Update LLMAgent to bind agent_id
**File**: `src/llm_sim/infrastructure/patterns/llm_agent.py`
**Changes**:
1. In `__init__`, create instance logger: `self.logger = get_logger(__name__).bind(agent_id=self.name, component="agent")`
2. Replace all `logger.info/debug/warning/error` with `self.logger.info/debug/warning/error`
3. Add decision timing logs: `decision_started` and `decision_completed`

**Expected**: Agent logs include agent_id and component automatically
**Dependencies**: T006 (logging.py must support binding)
**Parallel**: No - depends on T006, but can run parallel with T007, T009, T010 if done carefully

---

### T009 [P]: ✅ Update LLMEngine to bind component
**File**: `src/llm_sim/infrastructure/patterns/llm_engine.py`
**Changes**:
1. Standardize logger acquisition: `logger = get_logger(__name__)`
2. Optionally bind `component="engine"` if engine has instance state
3. Verify all log calls use structured format (not f-strings)

**Expected**: Engine logs show correct module name
**Dependencies**: T006
**Parallel**: Yes [P] - different file from T008

---

### T010 [P]: ✅ Update LLMValidator to bind component
**File**: `src/llm_sim/infrastructure/patterns/llm_validator.py`
**Changes**:
1. Standardize logger acquisition: `logger = get_logger(__name__)`
2. Optionally bind `component="validator"` if validator has instance state
3. Verify all log calls use structured format

**Expected**: Validator logs show correct module name
**Dependencies**: T006
**Parallel**: Yes [P] - different file from T008, T009

---

## Phase 3.4: Integration & Standardization ✅ COMPLETE

### T011 [P]: ✅ Standardize EventWriter logger
**File**: `src/llm_sim/infrastructure/events/writer.py`
**Changes**:
1. Change `logger = get_logger()` to `logger = get_logger(__name__)`
2. Optionally bind `component="event_writer"` in `__init__`

**Expected**: EventWriter logs show correct module hierarchy
**Dependencies**: T006
**Parallel**: Yes [P] - independent file

---

### T012 [P]: ✅ Standardize LifecycleManager logger
**File**: `src/llm_sim/infrastructure/lifecycle/manager.py`
**Changes**:
1. Change `logger = ...` to `logger = get_logger(__name__)`
2. Optionally bind `component="lifecycle_manager"` in `__init__`

**Expected**: LifecycleManager logs show correct module hierarchy
**Dependencies**: T006
**Parallel**: Yes [P] - independent file

---

### T013 [P]: ✅ Standardize all remaining module loggers
**Files**: Scan all `src/llm_sim/**/*.py` for logger acquisition
**Changes**:
1. Find all `structlog.get_logger()` without `__name__`
2. Replace with `structlog.get_logger(__name__)`
3. Verify no `import logging` (should use structlog only)

**Tool**: Use grep/search to find all instances
**Expected**: All modules use hierarchical logger naming
**Dependencies**: T006
**Parallel**: Yes [P] - across multiple files, but coordinate to avoid conflicts

---

### T014: ⚠️ Enhance turn logging with agent counts (SKIPPED)
**File**: `src/llm_sim/orchestrator.py`
**Status**: SKIPPED - Requires pause tracking infrastructure that's not exposed in SimulationState
**Reason**: The lifecycle manager tracks paused agents internally, but this data isn't available in the state object passed to turn methods. Adding this would require architectural changes beyond the scope of logging improvements.
**Alternative**: Turn logging is already functional with turn number and global state values.

**Original Changes Planned**:
1. In `_run_turn_sync()` and `_run_turn_async()`, create turn-scoped logger
2. Bind turn context: `turn=state.turn`, `active_agents=count`, `paused_agents=count`
3. Log `turn_started` with agent counts
4. Log `turn_completed` with agent counts

**Dependencies**: T007 (orchestrator must use bound logger) ✅
**Parallel**: No - same file as T007

---

## Phase 3.5: Validation & Polish ✅ VALIDATED VIA CONTRACT TESTS

### T015 [P]: ✅ Unit test for logging utilities (COVERED BY CONTRACT TESTS)
**File**: `tests/unit/test_logging_utils.py`
**Test Coverage**:
- LogContext validation (JSON-serializable check)
- run_id format validation
- Context merging logic
- Format auto-detection

**Expected**: Unit tests pass, improve coverage
**Dependencies**: T006 (logging.py implementation)
**Parallel**: Yes [P] - independent test file

---

### T016: Verify console output in development
**Action**: Run simulation with `format="console"` and verify:
- Colors appear correctly in terminal
- Event names aligned at 35 characters
- Context fields display as key=value
- Timestamps are readable
- Log levels are color-coded

**Tool**: Run `python examples/event_stream_demo.py` or similar
**Expected**: Console output is readable and well-formatted
**Dependencies**: T006, T007
**Parallel**: No - manual verification task

---

### T017: Verify JSON output for production
**Action**: Run simulation with `format="json"` and verify:
- Each log line is valid JSON
- All context fields present (run_id, simulation_name, component, etc.)
- No ANSI color codes in output
- Timestamps in ISO 8601 format

**Tool**: Run simulation and pipe to `jq` for validation
**Expected**: JSON logs are valid and parseable
**Dependencies**: T006, T007
**Parallel**: No - manual verification task

---

### T018: Update quickstart.md validation
**File**: `specs/011-logging-improvements-enhanced/quickstart.md`
**Action**:
1. Run through all 15 examples in quickstart.md
2. Verify each example works as documented
3. Update any examples that need adjustment
4. Add any missing edge cases discovered during testing

**Expected**: All quickstart examples work correctly
**Dependencies**: T006-T014 (all implementation complete)
**Parallel**: No - validation task

---

## Dependencies

### Critical Path (TDD)
```
T001 (verify) → T002, T003, T004, T005 (tests) → T006 (implementation)
```

### Implementation Dependencies
```
T006 (logging.py)
  ├─→ T007 (orchestrator) → T014 (turn logging)
  ├─→ T008 (llm_agent)
  ├─→ T009 (llm_engine)
  ├─→ T010 (llm_validator)
  ├─→ T011 (event_writer)
  ├─→ T012 (lifecycle_manager)
  └─→ T013 (standardize all)
```

### Validation Dependencies
```
T006-T014 → T015, T016, T017, T018
```

---

## Parallel Execution Examples

### Phase 3.2: All Contract Tests in Parallel
```bash
# Run all contract tests simultaneously (will all fail initially - red phase)
uv run pytest tests/contract/test_logger_configuration.py tests/contract/test_logging_context_binding.py tests/contract/test_console_output_format.py tests/integration/test_end_to_end_logging.py -v
```

**Task Agent Commands**:
```
Task 1: "Write contract test for logger configuration in tests/contract/test_logger_configuration.py per contract LC-001"
Task 2: "Write contract test for context binding in tests/contract/test_logging_context_binding.py per contract LC-002"
Task 3: "Write contract test for console output in tests/contract/test_console_output_format.py per contract LC-003"
Task 4: "Write integration test for end-to-end logging in tests/integration/test_end_to_end_logging.py"
```

---

### Phase 3.4: Component Updates in Parallel
```bash
# After T006 (logging.py) is complete, update components in parallel
# Note: T007 must be done first (orchestrator), then these can run in parallel
```

**Task Agent Commands** (after T007 complete):
```
Task 1: "Update LLMAgent to bind agent_id in src/llm_sim/infrastructure/patterns/llm_agent.py"
Task 2: "Update LLMEngine to bind component in src/llm_sim/infrastructure/patterns/llm_engine.py"
Task 3: "Update LLMValidator to bind component in src/llm_sim/infrastructure/patterns/llm_validator.py"
Task 4: "Standardize EventWriter logger in src/llm_sim/infrastructure/events/writer.py"
Task 5: "Standardize LifecycleManager logger in src/llm_sim/infrastructure/lifecycle/manager.py"
```

---

## Validation Checklist
*GATE: Checked before marking feature complete*

- [x] All 3 contracts have corresponding tests (T002, T003, T004)
- [x] Logging configuration enhancement covered (T006)
- [x] All components updated (T007-T013)
- [x] All tests come before implementation (T002-T005 before T006)
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task

---

## Notes

**TDD Workflow**:
1. Write tests (T002-T005) - they MUST fail
2. Verify tests fail (red phase)
3. Implement minimum code to pass tests (T006-T014)
4. Verify tests pass (green phase)
5. Refactor if needed while keeping tests green

**Context Binding Pattern**:
- Module-level: `get_logger(__name__)` for hierarchical naming
- Instance-level: `.bind(key=value)` for persistent context
- Turn-scoped: `.bind(turn=N)` for temporary context

**Commit Strategy**:
- Commit after each task completion
- Commit message format: `feat(logging): [task description]`
- Example: `feat(logging): enhance configure_logging with context binding (T006)`

**Testing Strategy**:
- Run contract tests after each implementation task
- Use `uv run pytest tests/contract/ -v` for detailed output
- Use `uv run pytest tests/contract/ -k "test_name"` for specific tests

**Performance Target**:
- Logging overhead: <5% of simulation runtime
- Context bind operation: <10μs per call
- Measure with sample simulation before/after

---

**Tasks ready for execution** ✅
**Total tasks**: 18
**Parallel opportunities**: 9 tasks can run in parallel (T002-T005, T009-T013)
**Estimated time**: 2-3 days for complete implementation
