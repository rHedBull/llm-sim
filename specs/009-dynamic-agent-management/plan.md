
# Implementation Plan: Dynamic Agent Management

**Branch**: `009-dynamic-agent-management` | **Date**: 2025-10-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-dynamic-agent-management/spec.md`

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
Enable dynamic control of agent populations during simulation runtime through three core operations (add, remove, pause/resume) with two control mechanisms (agent-initiated and external orchestrator control). Agents are stored by unique names with automatic collision resolution, lifecycle changes apply after turn execution, and validation ensures technical feasibility within a 25-agent maximum.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (data models), PyYAML 6.x (config), structlog 24.x (logging)
**Storage**: JSON checkpoint files in `output/` directory
**Testing**: pytest with coverage, contract tests, integration tests
**Target Platform**: Linux/macOS/Windows (cross-platform Python)
**Project Type**: single (simulation framework library)
**Performance Goals**: Support 25 concurrent agents, handle lifecycle operations in O(1) time per agent
**Constraints**: Maximum 25 agents, lifecycle changes atomic per turn, maintain state consistency
**Scale/Scope**: Framework component affecting orchestrator, engine, state management, and persistence layers

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: KISS (Simplicity First)
- ✅ **PASS**: Agent storage migrates from list to dict (simple, standard data structure)
- ✅ **PASS**: Pause tracking uses a set (simple collection, O(1) lookup)
- ✅ **PASS**: Lifecycle actions separated from regular actions (clear separation of concerns)
- ✅ **PASS**: Auto-rename collision resolution using numeric suffixes (straightforward algorithm)

### Principle 2: DRY (Single Source of Truth)
- ✅ **PASS**: Agent storage in single dict eliminates duplicate tracking
- ✅ **PASS**: Validation logic centralized in lifecycle manager (no duplication across operations)
- ✅ **PASS**: State snapshots reflect single authoritative agent population

### Principle 3: No Legacy Support
- ✅ **PASS**: List-to-dict migration is breaking change (no compatibility layer)
- ✅ **PASS**: Old code must update to new dict-based access patterns
- ✅ **PASS**: No silent fallbacks for legacy list-based agent access

### Principle 4: Test-First Development (TDD)
- ✅ **PASS**: Contract tests will be written before implementation
- ✅ **PASS**: Integration tests for each acceptance scenario
- ✅ **PASS**: Unit tests for validation logic, collision resolution, pause tracking

### Principle 5: Clean Interface Design
- ✅ **PASS**: All lifecycle methods type-annotated (add_agent, remove_agent, pause_agent, resume_agent)
- ✅ **PASS**: Single responsibility per operation (add != remove != pause != resume)
- ✅ **PASS**: Explicit state changes (paused status, agent presence/absence)

### Principle 6: Observability and Debugging
- ✅ **PASS**: Lifecycle validation failures logged as warnings (FR-029)
- ✅ **PASS**: Structured logging for all lifecycle operations (add, remove, pause, resume)
- ✅ **PASS**: Clear error messages for constraint violations (max count, duplicate names)

### Principle 7: Python Package Management with uv
- ✅ **PASS**: All tests run via `uv run pytest`
- ✅ **PASS**: Development tools invoked through `uv run` (black, mypy, ruff)
- ✅ **PASS**: No new dependencies required (uses existing Pydantic, PyYAML, structlog)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── models/
│   ├── state.py                    # [MODIFY] Change agents: List → Dict[str, Agent]
│   ├── action.py                   # [MODIFY] Add lifecycle action types
│   └── lifecycle.py                # [NEW] Lifecycle action models
├── orchestrator.py                 # [MODIFY] Add lifecycle management methods
├── infrastructure/
│   ├── base/
│   │   └── engine.py              # [MODIFY] Separate lifecycle from regular actions
│   └── lifecycle/
│       ├── __init__.py            # [NEW] Lifecycle subsystem
│       ├── manager.py             # [NEW] Lifecycle operation coordinator
│       ├── validator.py           # [NEW] Lifecycle validation logic
│       └── pause_tracker.py       # [NEW] Pause/resume state tracking
└── persistence/
    └── checkpoint_manager.py       # [MODIFY] Support dict-based agent serialization

tests/
├── contract/
│   └── test_lifecycle_contracts.py # [NEW] Contract tests for lifecycle operations
├── integration/
│   ├── test_dynamic_agents.py      # [NEW] End-to-end lifecycle scenarios
│   └── test_pause_resume.py        # [NEW] Pause/resume integration tests
└── unit/
    ├── test_lifecycle_manager.py   # [NEW] Unit tests for lifecycle manager
    ├── test_lifecycle_validator.py # [NEW] Unit tests for validation logic
    ├── test_pause_tracker.py       # [NEW] Unit tests for pause tracking
    └── test_state_dict_migration.py # [NEW] Unit tests for list→dict migration
```

**Structure Decision**: Single project (Python simulation framework). New `infrastructure/lifecycle/` subsystem contains lifecycle management logic separate from core simulation loop. State model migrates from list-based to dict-based agent storage. Tests follow TDD with contracts → integration → implementation pattern.

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

1. **Contract Tests** (from `/contracts/*.md`):
   - Test `LifecycleManager.add_agent()` contract [P]
   - Test `LifecycleManager.remove_agent()` contract [P]
   - Test `LifecycleManager.pause_agent()` contract [P]
   - Test `LifecycleManager.resume_agent()` contract [P]
   - Test `PauseTracker.pause()` contract [P]
   - Test `PauseTracker.resume()` contract [P]
   - Test `PauseTracker.tick_auto_resume()` contract [P]

2. **Model Creation** (from `data-model.md`):
   - Create `LifecycleAction` model [P]
   - Create `ValidationResult` model [P]
   - Create `LifecycleOperation` enum [P]
   - Modify `SimulationState`: List → Dict agent storage
   - Add paused agent tracking fields to `SimulationState`

3. **Core Implementation** (TDD order - test → implement):
   - Implement `PauseTracker` class
   - Implement `LifecycleValidator` class
   - Implement `LifecycleManager` class
   - Modify `SimulationOrchestrator` to use `LifecycleManager`
   - Modify `Engine` to separate lifecycle actions

4. **Integration Tests** (from acceptance scenarios in spec):
   - Test add agent at runtime (scenario 1)
   - Test remove agent at runtime (scenario 2)
   - Test pause agent (scenario 3)
   - Test resume agent (scenario 4)
   - Test agent self-removal (scenario 5)
   - Test agent spawning (scenario 6)
   - Test auto-resume after N turns (scenario 7)
   - Test multiple lifecycle changes in one turn (scenario 8)

5. **Edge Case Tests** (from spec edge cases):
   - Test duplicate name collision resolution
   - Test max agent limit (25)
   - Test pause already-paused agent
   - Test resume non-paused agent
   - Test last agent removal

6. **Persistence** (checkpoint serialization):
   - Modify `CheckpointManager` for dict-based agents
   - Test checkpoint serialization with paused agents
   - Test checkpoint deserialization with auto-resume

7. **Migration** (breaking changes):
   - Update all agent iteration patterns
   - Update agent access patterns from list to dict
   - Run full test suite to catch migration issues

**Ordering Strategy**:
- TDD: Contract tests → Models → Core → Integration
- Dependencies: `PauseTracker` (no deps) → `LifecycleValidator` → `LifecycleManager` → Orchestrator integration
- Parallel opportunities: All contract tests [P], model creation [P]
- Critical path: State migration → Lifecycle manager → Engine integration

**Estimated Output**: ~35 numbered tasks in dependency order

**Key Dependencies**:
- State migration must complete before lifecycle manager tests
- PauseTracker must exist before LifecycleManager
- Contract tests can run in parallel (independent)

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
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (all 7 principles compliant)
- [x] Post-Design Constitution Check: PASS (verified after Phase 1)
- [x] All NEEDS CLARIFICATION resolved (5 clarifications documented)
- [x] Complexity deviations documented (none - all within constitutional bounds)

**Artifacts Generated**:
- [x] `research.md` - Technical decisions and design patterns
- [x] `data-model.md` - Entity definitions and relationships
- [x] `contracts/lifecycle_manager_contract.md` - LifecycleManager interface spec
- [x] `contracts/pause_tracker_contract.md` - PauseTracker interface spec
- [x] `quickstart.md` - End-to-end validation guide
- [x] `CLAUDE.md` - Updated agent context (Python 3.12, Pydantic, PyYAML, structlog)

**Next Command**: `/tasks` - Generate task breakdown from Phase 2 strategy

---
*Based on Constitution v1.3.0 - See `.specify/memory/constitution.md`*
