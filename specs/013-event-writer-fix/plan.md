
# Implementation Plan: EventWriter Synchronous Mode Implementation

**Branch**: `013-event-writer-fix` | **Date**: 2025-10-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/hendrik/coding/llm_sim/llm_sim/specs/013-event-writer-fix/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Add synchronous write mode to EventWriter class to fix missing events.jsonl files. The current async implementation queues events but they're never written because the simulation's `_run_turn_sync()` blocks the event loop, preventing the background writer task from executing. The solution adds a sync mode that writes events immediately to disk while preserving backward compatibility with the existing async mode.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (data models), structlog 24.x (logging), aiofiles (async I/O for async mode)
**Storage**: File system (JSONL files in `output/{run_id}/events.jsonl`)
**Testing**: pytest with asyncio support
**Target Platform**: Linux (primary), cross-platform compatible
**Project Type**: single (Python library/framework)
**Performance Goals**:
  - Sync mode: ~1000 events/sec (with fsync guarantees)
  - Async mode: ~100,000 events/sec (queue-based)
  - Current scale: ~200 events per simulation run (20 turns × 4 agents × ~2-3 events)
**Constraints**:
  - Must work in sync execution contexts (blocked event loop)
  - Zero breaking changes to existing async API
  - Must guarantee event persistence in sync mode
  - File rotation at 500MB threshold
**Scale/Scope**:
  - Single EventWriter class modification
  - Two new methods (_write_event_sync, _rotate_file_sync)
  - Mode enum addition (WriteMode.SYNC, WriteMode.ASYNC)
  - Orchestrator integration (1 line change)
  - ~150 lines of new code
  - 4 unit tests, 1 integration test

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: KISS (Keep It Simple and Stupid)
✅ **PASS** - Solution adds minimal complexity (2 new methods, 1 enum, mode parameter)
- Single class modification (EventWriter)
- Simple branching logic in emit() method
- No new dependencies or abstractions
- Preserves existing async implementation unchanged

### Principle 2: DRY (Don't Repeat Yourself)
✅ **PASS** - No duplication introduced
- Sync and async paths share verbosity filtering logic
- File rotation logic is separate (sync vs async) due to fundamentally different I/O patterns
- emit() interface unified across both modes

### Principle 3: No Legacy Support
✅ **PASS** - Explicit mode selection, no silent fallbacks
- Default mode is async (preserves existing behavior)
- Mode must be explicitly set at initialization
- No automatic detection or silent mode switching
- Both modes use same Event model (no legacy format support)

### Principle 4: Test-First Development
✅ **COMMITTED** - Tests will be written before implementation
- Unit tests for sync mode write operations
- Unit tests for file rotation in sync mode
- Unit tests for mode selection
- Integration test for sync simulation end-to-end
- All tests must fail initially (red phase)

### Principle 5: Clean Interface Design
✅ **PASS** - Explicit, type-annotated interface
- WriteMode enum makes mode selection explicit
- All public methods retain type annotations
- emit() signature unchanged (polymorphic behavior)
- State changes (mode) are obvious from constructor signature
- Single responsibility maintained (write events, rotate files)

### Principle 6: Observability and Debugging
✅ **PASS** - Enhanced logging for both modes
- Mode selection logged at initialization
- Sync mode logs file writes with mode indicator
- Errors include mode context ("sync" vs "async")
- Rotation events include mode and size information
- Debug-friendly (sync mode writes are immediately visible on disk)

### Principle 7: Python Package Management with uv
✅ **PASS** - No new dependencies, existing uv workflow
- No new package dependencies required
- Tests will run via `uv run pytest`
- Development uses existing `uv` setup
- No changes to pyproject.toml needed

## Project Structure

### Documentation (this feature)
```
specs/013-event-writer-fix/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   └── event_writer_interface.py  # Public API contract
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── infrastructure/
│   └── events/
│       ├── writer.py           # MODIFY: Add sync mode support
│       ├── config.py           # Existing (VerbosityLevel, should_log_event)
│       └── __init__.py         # UPDATE: Export WriteMode enum
├── orchestrator.py             # MODIFY: Use WriteMode.SYNC
└── models/
    └── event.py                # Existing (Event model)

tests/
├── unit/
│   └── infrastructure/
│       └── events/
│           ├── test_event_writer_async.py    # Existing async tests
│           └── test_event_writer_sync.py     # NEW: Sync mode tests
└── integration/
    └── test_sync_simulation_events.py         # NEW: End-to-end test
```

**Structure Decision**: Single project structure (Python library). All changes are localized to the events infrastructure module with minimal orchestrator integration. No new modules or packages required - this is a targeted enhancement to existing EventWriter class.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load task template**: `.specify/templates/tasks-template.md`

2. **Generate test tasks from contracts** (contracts/event_writer_interface.py):
   - Task: Write test_sync_mode_writes_immediately [P]
   - Task: Write test_sync_mode_file_rotation [P]
   - Task: Write test_sync_mode_no_async_dependency [P]
   - Task: Write test_mode_selection [P]
   - Task: Write test_sync_simulation_creates_events (integration) [P]
   - Estimated: 5 test tasks

3. **Generate implementation tasks from data model**:
   - Task: Add WriteMode enum to writer.py
   - Task: Add mode parameter to EventWriter.__init__
   - Task: Implement _write_event_sync method
   - Task: Implement _rotate_file_sync method
   - Task: Update emit() to dispatch by mode
   - Task: Update start() for sync mode no-op
   - Task: Update stop() for sync mode no-op
   - Estimated: 7 implementation tasks

4. **Generate integration tasks**:
   - Task: Export WriteMode from __init__.py
   - Task: Update orchestrator to use WriteMode.SYNC
   - Task: Run full test suite to verify no regressions
   - Estimated: 3 integration tasks

5. **Generate validation tasks from quickstart.md**:
   - Task: Execute quickstart validation steps 1-7
   - Task: Run manual simulation test
   - Task: Verify performance benchmarks
   - Estimated: 3 validation tasks

**Ordering Strategy** (TDD order):
```
Phase A: Setup (Parallel)
  [P] Task 1: Add WriteMode enum
  [P] Task 2: Export WriteMode from __init__.py

Phase B: Test Writing (Parallel - Red Phase)
  [P] Task 3: Write test_sync_mode_writes_immediately
  [P] Task 4: Write test_sync_mode_file_rotation
  [P] Task 5: Write test_sync_mode_no_async_dependency
  [P] Task 6: Write test_mode_selection
  [P] Task 7: Write test_sync_simulation_creates_events

Phase C: Run Tests (Verify Red)
  Task 8: Run tests - EXPECT FAILURES (red phase)

Phase D: Implementation (Green Phase)
  Task 9: Add mode parameter to EventWriter.__init__
  Task 10: Implement _write_event_sync method
  Task 11: Implement _rotate_file_sync method
  Task 12: Update emit() to dispatch by mode
  Task 13: Update start() for sync mode no-op
  Task 14: Update stop() for sync mode no-op

Phase E: Integration
  Task 15: Update orchestrator to use WriteMode.SYNC
  Task 16: Run all tests - EXPECT PASS (green phase)

Phase F: Validation
  Task 17: Execute quickstart validation (steps 1-7)
  Task 18: Run performance benchmarks
```

**Estimated Output**: 18 numbered, ordered tasks in tasks.md

**Task Parallelization**:
- Phase A: 2 tasks in parallel (independent files)
- Phase B: 5 tasks in parallel (independent test files)
- Phase D: Sequential (all modify writer.py)
- Total parallel opportunities: 7 tasks
- Sequential dependencies: 11 tasks

**Success Criteria for /tasks Command**:
- All 18 tasks generated with clear descriptions
- TDD order enforced (tests before implementation)
- Parallel tasks marked with [P]
- Each task references specific file and line numbers where applicable
- Validation tasks reference quickstart.md steps

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md created
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md created
- [x] Phase 2: Task planning complete (/plan command - approach described, 18 tasks planned)
- [x] Phase 3: Tasks generated (/tasks command) - tasks.md created with 18 tasks
- [x] Phase 4: Implementation complete (/implement command) - All 18 tasks completed
- [x] Phase 5: Validation passed - Unit tests 4/4 passing, quickstart validation complete

**Gate Status**:
- [x] Initial Constitution Check: PASS (all 7 principles satisfied)
- [x] Post-Design Constitution Check: PASS (re-evaluated after design phase)
- [x] All NEEDS CLARIFICATION resolved (none in technical context, FR-019 resolved via research)
- [x] Complexity deviations documented (none - no violations)

**Artifacts Generated**:
- [x] specs/013-event-writer-fix/research.md
- [x] specs/013-event-writer-fix/data-model.md
- [x] specs/013-event-writer-fix/contracts/event_writer_interface.py
- [x] specs/013-event-writer-fix/quickstart.md
- [x] specs/013-event-writer-fix/tasks.md (18 tasks, TDD order)
- [x] CLAUDE.md updated with new tech context

---
*Based on Constitution v1.3.0 - See `.specify/memory/constitution.md`*
