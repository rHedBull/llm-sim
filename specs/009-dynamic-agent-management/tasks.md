# Tasks: Dynamic Agent Management

**Input**: Design documents from `/specs/009-dynamic-agent-management/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Tech Stack**: Python 3.12, Pydantic 2.x, PyYAML 6.x, structlog 24.x, pytest
**Testing Strategy**: TDD with contract tests → models → integration tests → implementation

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.12, Pydantic, PyYAML, structlog
   → Structure: Single project (src/llm_sim/, tests/)
2. Load design documents ✓
   → data-model.md: 5 entities + SimulationState modifications
   → contracts/: 2 contract files (LifecycleManager, PauseTracker)
   → research.md: Dict storage, lifecycle separation, pause tracking
   → quickstart.md: 5 validation scenarios
3. Generate tasks by category ✓
   → Setup: Project structure, linting
   → Tests: 7 contract tests, 8 integration tests, 5 edge case tests
   → Core: 5 new components, 5 modified components
   → Integration: Orchestrator, engine, persistence
   → Polish: Migration, cleanup, documentation
4. Apply task rules ✓
   → Different files = [P] for parallel
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T040) ✓
6. Dependency graph generated ✓
7. Parallel execution examples included ✓
8. Validation complete ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All paths relative to repository root

---

## Phase 3.1: Setup (Prerequisites)

### T001: Create lifecycle subsystem structure
**Path**: `src/llm_sim/infrastructure/lifecycle/`
**Action**: Create directory and `__init__.py`
```bash
mkdir -p src/llm_sim/infrastructure/lifecycle
touch src/llm_sim/infrastructure/lifecycle/__init__.py
```

### T002: [P] Configure test structure for lifecycle
**Path**: `tests/contract/`, `tests/integration/`, `tests/unit/`
**Action**: Ensure test directories exist (likely already present)
```bash
mkdir -p tests/contract tests/integration tests/unit
```

### T003: [P] Verify development tools
**Path**: Repository root
**Action**: Confirm uv, pytest, black, mypy, ruff configured
```bash
uv run pytest --version
uv run black --version
uv run mypy --version
```

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel - Different Files)

#### T004: [P] Contract test: PauseTracker.pause()
**Path**: `tests/contract/test_pause_tracker_pause.py`
**Contract**: `contracts/pause_tracker_contract.md` - `pause()` method
**Action**: Test preconditions, postconditions, side effects
- Agent added to `paused_agents` set
- Auto-resume metadata set if provided
- No validation performed (assumes pre-validated)

#### T005: [P] Contract test: PauseTracker.resume()
**Path**: `tests/contract/test_pause_tracker_resume.py`
**Contract**: `contracts/pause_tracker_contract.md` - `resume()` method
**Action**: Test returns True/False, removes from paused set and auto_resume dict

#### T006: [P] Contract test: PauseTracker.tick_auto_resume()
**Path**: `tests/contract/test_pause_tracker_tick.py`
**Contract**: `contracts/pause_tracker_contract.md` - `tick_auto_resume()` method
**Action**: Test counter decrement, auto-resume at 0, list of resumed agents

#### T007: [P] Contract test: LifecycleManager.add_agent()
**Path**: `tests/contract/test_lifecycle_manager_add.py`
**Contract**: `contracts/lifecycle_manager_contract.md` - `add_agent()` method
**Action**: Test collision resolution, max agent limit (25), resolved name return

#### T008: [P] Contract test: LifecycleManager.remove_agent()
**Path**: `tests/contract/test_lifecycle_manager_remove.py`
**Contract**: `contracts/lifecycle_manager_contract.md` - `remove_agent()` method
**Action**: Test agent removal from dict, paused set, auto_resume dict

#### T009: [P] Contract test: LifecycleManager.pause_agent()
**Path**: `tests/contract/test_lifecycle_manager_pause.py`
**Contract**: `contracts/lifecycle_manager_contract.md` - `pause_agent()` method
**Action**: Test pause addition, auto_resume configuration, validation failures

#### T010: [P] Contract test: LifecycleManager.resume_agent()
**Path**: `tests/contract/test_lifecycle_manager_resume.py`
**Contract**: `contracts/lifecycle_manager_contract.md` - `resume_agent()` method
**Action**: Test resume removal from paused set, validation failures

### Integration Tests (Parallel - Different Files)

#### T011: [P] Integration test: Add agent at runtime (Scenario 1)
**Path**: `tests/integration/test_add_agent_runtime.py`
**Scenario**: Acceptance scenario 1 from spec.md
**Action**: Test adding agent with initial state, agent participates in next turn

#### T012: [P] Integration test: Remove agent at runtime (Scenario 2)
**Path**: `tests/integration/test_remove_agent_runtime.py`
**Scenario**: Acceptance scenario 2 from spec.md
**Action**: Test agent removal, no future participation, data excluded

#### T013: [P] Integration test: Pause agent (Scenario 3)
**Path**: `tests/integration/test_pause_agent.py`
**Scenario**: Acceptance scenario 3 from spec.md
**Action**: Test agent skips turns, state retained

#### T014: [P] Integration test: Resume agent (Scenario 4)
**Path**: `tests/integration/test_resume_agent.py`
**Scenario**: Acceptance scenario 4 from spec.md
**Action**: Test agent resumes from preserved state

#### T015: [P] Integration test: Agent self-removal (Scenario 5)
**Path**: `tests/integration/test_agent_self_removal.py`
**Scenario**: Acceptance scenario 5 from spec.md
**Action**: Test agent requests own removal, validation passes, agent removed

#### T016: [P] Integration test: Agent spawning (Scenario 6)
**Path**: `tests/integration/test_agent_spawning.py`
**Scenario**: Acceptance scenario 6 from spec.md
**Action**: Test agent spawns new agent, count < 25, validation passes

#### T017: [P] Integration test: Auto-resume after N turns (Scenario 7)
**Path**: `tests/integration/test_auto_resume.py`
**Scenario**: Acceptance scenario 7 from spec.md
**Action**: Test paused agent auto-resumes after specified turns

#### T018: [P] Integration test: Multiple lifecycle changes in one turn (Scenario 8)
**Path**: `tests/integration/test_multiple_lifecycle_changes.py`
**Scenario**: Acceptance scenario 8 from spec.md
**Action**: Test atomic application of all lifecycle changes after turn

### Edge Case Tests (Parallel - Different Files)

#### T019: [P] Edge case test: Duplicate name collision
**Path**: `tests/unit/test_name_collision.py`
**Edge Case**: Auto-rename with numeric suffix
**Action**: Test `agent` → `agent_1` → `agent_2` pattern

#### T020: [P] Edge case test: Max agent limit (25)
**Path**: `tests/unit/test_max_agent_limit.py`
**Edge Case**: Validation failure when adding 26th agent
**Action**: Test validation fails, logs warning, agent not added

#### T021: [P] Edge case test: Pause already-paused agent
**Path**: `tests/unit/test_pause_already_paused.py`
**Edge Case**: Validation failure, logged warning
**Action**: Test returns False, logs warning

#### T022: [P] Edge case test: Resume non-paused agent
**Path**: `tests/unit/test_resume_non_paused.py`
**Edge Case**: Validation failure, logged warning
**Action**: Test returns False, logs warning

#### T023: [P] Edge case test: Last agent removal
**Path**: `tests/unit/test_last_agent_removal.py`
**Edge Case**: Allowed (simulation can have 0 agents)
**Action**: Test agent removed successfully, state has 0 agents

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

**Dependency**: All Phase 3.2 tests must be written and failing

### Models (Parallel - Different Files)

#### T024: [P] Create LifecycleOperation enum
**Path**: `src/llm_sim/models/lifecycle.py`
**Data Model**: `data-model.md` - LifecycleOperation enum
**Action**: Define `ADD_AGENT`, `REMOVE_AGENT`, `PAUSE_AGENT`, `RESUME_AGENT`

#### T025: [P] Create LifecycleAction model
**Path**: `src/llm_sim/models/lifecycle.py`
**Data Model**: `data-model.md` - LifecycleAction entity
**Action**: Pydantic model with operation, initiating_agent, target_agent_name, initial_state, auto_resume_turns

#### T026: [P] Create ValidationResult model
**Path**: `src/llm_sim/models/lifecycle.py`
**Data Model**: `data-model.md` - ValidationResult entity
**Action**: Pydantic model with valid, reason, warnings fields

#### T027: Modify SimulationState: agents List → Dict
**Path**: `src/llm_sim/models/state.py`
**Data Model**: `data-model.md` - SimulationState modifications
**Action**: Change `agents: List[Agent]` to `agents: Dict[str, Agent]`
**Breaking Change**: Migration required for existing code

#### T028: Add pause tracking fields to SimulationState
**Path**: `src/llm_sim/models/state.py`
**Data Model**: `data-model.md` - SimulationState new fields
**Action**: Add `paused_agents: Set[str]`, `auto_resume: Dict[str, int]`
**Depends On**: T027 (same file)

### Core Components (Sequential - Dependencies)

#### T029: Implement PauseTracker class
**Path**: `src/llm_sim/infrastructure/lifecycle/pause_tracker.py`
**Data Model**: `data-model.md` - PauseTracker entity
**Contract**: `contracts/pause_tracker_contract.md`
**Action**: Implement pause(), resume(), is_paused(), tick_auto_resume(), serialization
**Makes Pass**: T004, T005, T006

#### T030: Implement LifecycleValidator class
**Path**: `src/llm_sim/infrastructure/lifecycle/validator.py`
**Data Model**: `data-model.md` - LifecycleValidator entity
**Action**: Implement validate_add(), validate_remove(), validate_pause(), validate_resume()
**Depends On**: T024, T025, T026 (model dependencies)

#### T031: Implement LifecycleManager class
**Path**: `src/llm_sim/infrastructure/lifecycle/manager.py`
**Data Model**: `data-model.md` - LifecycleManager entity
**Contract**: `contracts/lifecycle_manager_contract.md`
**Action**: Implement add_agent(), remove_agent(), pause_agent(), resume_agent(), get_active_agents(), process_auto_resume()
**Depends On**: T029, T030
**Makes Pass**: T007, T008, T009, T010

---

## Phase 3.4: Integration

**Dependency**: Phase 3.3 core implementation complete

#### T032: Integrate LifecycleManager with SimulationOrchestrator
**Path**: `src/llm_sim/orchestrator.py`
**Plan**: `plan.md` - Orchestrator modifications
**Action**: Add lifecycle_manager instance, expose add_agent(), remove_agent(), pause_agent(), resume_agent() methods
**Makes Pass**: T011, T012, T013, T014

#### T033: Modify Engine to separate lifecycle actions
**Path**: `src/llm_sim/infrastructure/base/engine.py`
**Plan**: `plan.md` - Engine modifications
**Action**: Extract lifecycle actions in separate phase after regular actions
**Makes Pass**: T015, T016, T018

#### T034: Implement process_auto_resume in turn execution
**Path**: `src/llm_sim/orchestrator.py` or `engine.py`
**Action**: Call lifecycle_manager.process_auto_resume() at turn start
**Depends On**: T032
**Makes Pass**: T017

#### T035: Update CheckpointManager for dict-based agent serialization
**Path**: `src/llm_sim/persistence/checkpoint_manager.py`
**Plan**: `plan.md` - Persistence modifications
**Action**: Serialize agents dict, paused_agents set, auto_resume dict
**Depends On**: T027, T028

---

## Phase 3.5: Migration & Polish

**Dependency**: Phase 3.4 integration complete

#### T036: Migrate agent iteration patterns (list → dict)
**Path**: All files accessing `state.agents`
**Action**: Update `for agent in state.agents` → `for agent in state.agents.values()`
**Breaking Change**: Find all occurrences, update systematically
**Verification**: `uv run grep -r "for agent in.*\.agents[^.]" src/`

#### T037: Migrate agent access patterns (index → name)
**Path**: All files accessing agents by index
**Action**: Update `state.agents[i]` → `state.agents[name]`
**Breaking Change**: Find all occurrences, update systematically
**Verification**: `uv run grep -r "\.agents\[" src/`

#### T038: [P] Add unit tests for LifecycleValidator
**Path**: `tests/unit/test_lifecycle_validator.py`
**Action**: Unit tests for each validation method
**Depends On**: T030

#### T039: Run full test suite and fix regressions
**Path**: Repository root
**Action**: `uv run pytest tests/ -v --cov=src/llm_sim`
**Verification**: All tests pass, coverage ≥ 90% for lifecycle subsystem

#### T040: Execute quickstart validation scenarios
**Path**: `specs/009-dynamic-agent-management/quickstart.md`
**Action**: Run all 5 quickstart scripts, verify expected outputs
**Final Validation**: Feature complete and validated

---

## Dependencies

### Critical Path
```
Setup (T001-T003)
  ↓
Contract Tests (T004-T010) [PARALLEL]
Integration Tests (T011-T018) [PARALLEL]
Edge Case Tests (T019-T023) [PARALLEL]
  ↓
Models (T024-T026) [PARALLEL]
  ↓
State Migration (T027-T028) [SEQUENTIAL - same file]
  ↓
PauseTracker (T029)
  ↓
LifecycleValidator (T030)
  ↓
LifecycleManager (T031)
  ↓
Orchestrator Integration (T032)
Engine Integration (T033)
Auto-Resume Integration (T034)
Persistence (T035)
  ↓
Migration (T036-T037)
  ↓
Unit Tests (T038)
  ↓
Validation (T039-T040)
```

### Blocking Dependencies
- T028 blocks T029-T031 (needs pause tracking fields)
- T029, T030 block T031 (LifecycleManager needs both)
- T031 blocks T032-T034 (orchestrator/engine need LifecycleManager)
- T027 blocks T036-T037 (migration requires dict structure)
- T032-T035 block T039 (integration before full test suite)

### Parallel Opportunities
- **T004-T010**: All contract tests (7 tasks)
- **T011-T018**: All integration tests (8 tasks)
- **T019-T023**: All edge case tests (5 tasks)
- **T024-T026**: All model creation (3 tasks)
- **Total**: 23 tasks can run in parallel during test phase

---

## Parallel Execution Examples

### Example 1: Contract Tests (Phase 3.2)
```bash
# Launch all 7 contract tests in parallel:
uv run pytest tests/contract/test_pause_tracker_pause.py &
uv run pytest tests/contract/test_pause_tracker_resume.py &
uv run pytest tests/contract/test_pause_tracker_tick.py &
uv run pytest tests/contract/test_lifecycle_manager_add.py &
uv run pytest tests/contract/test_lifecycle_manager_remove.py &
uv run pytest tests/contract/test_lifecycle_manager_pause.py &
uv run pytest tests/contract/test_lifecycle_manager_resume.py &
wait
```

### Example 2: Integration Tests (Phase 3.2)
```bash
# Launch all 8 integration tests in parallel:
uv run pytest tests/integration/test_add_agent_runtime.py &
uv run pytest tests/integration/test_remove_agent_runtime.py &
uv run pytest tests/integration/test_pause_agent.py &
uv run pytest tests/integration/test_resume_agent.py &
uv run pytest tests/integration/test_agent_self_removal.py &
uv run pytest tests/integration/test_agent_spawning.py &
uv run pytest tests/integration/test_auto_resume.py &
uv run pytest tests/integration/test_multiple_lifecycle_changes.py &
wait
```

### Example 3: Model Creation (Phase 3.3)
```bash
# Create all 3 models in parallel (different sections of same file):
# Note: Actually sequential since same file, but can design in parallel
# Design LifecycleOperation enum
# Design LifecycleAction model
# Design ValidationResult model
# Then implement all in single commit to lifecycle.py
```

---

## Notes

### TDD Enforcement
- **CRITICAL**: All tests (T004-T023) MUST fail initially
- Verify failure: `uv run pytest tests/contract tests/integration tests/unit -v`
- Expected: All tests fail with import errors or assertion failures
- Only then proceed to implementation (T024+)

### Breaking Changes
- **T027**: `agents: List → Dict` requires updating all agent access
- **T036-T037**: Systematic migration of all references
- No legacy compatibility layer (Constitution Principle 3)

### Logging Contract
- All lifecycle operations log structured messages
- Validation failures: Warning level, non-blocking
- Successful operations: Info level
- Use structlog with operation, agent_name, turn fields

### Performance Targets
- All operations O(1) or O(n) where n ≤ 25
- Add agent: < 1ms (including collision resolution)
- Pause/Resume: < 1ms
- Turn execution: No measurable overhead for lifecycle processing

### Commit Strategy
- Commit after each task completion
- Test tasks: One commit per test file
- Implementation: One commit per component
- Migration: One commit for all patterns updated

---

## Validation Checklist

**Pre-Implementation** (Before T024):
- [x] All contracts have corresponding tests (T004-T010)
- [x] All entities have model tasks (T024-T028)
- [x] All tests come before implementation
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path

**Post-Implementation** (T039):
- [ ] All contract tests pass
- [ ] All integration tests pass
- [ ] All edge case tests pass
- [ ] Full test suite passes
- [ ] Coverage ≥ 90% for lifecycle subsystem
- [ ] Quickstart scenarios validate successfully
- [ ] No TODO or FIXME comments remain
- [ ] All logging structured and informative

**Migration Verification** (T036-T037):
- [ ] All `for agent in state.agents` patterns updated
- [ ] All `state.agents[index]` patterns updated
- [ ] No list-based access patterns remain
- [ ] Type checker passes (mypy)
- [ ] All existing tests still pass

---

## Task Execution Order (Recommended)

**Week 1: Tests (TDD Foundation)**
1. Setup (T001-T003)
2. Contract tests (T004-T010) - Parallel
3. Integration tests (T011-T018) - Parallel
4. Edge case tests (T019-T023) - Parallel
5. Verify all tests fail

**Week 2: Core Implementation**
6. Models (T024-T026) - Parallel design, sequential commit
7. State migration (T027-T028) - Sequential (same file)
8. PauseTracker (T029)
9. LifecycleValidator (T030)
10. LifecycleManager (T031)
11. Verify contract tests pass

**Week 3: Integration**
12. Orchestrator integration (T032)
13. Engine integration (T033)
14. Auto-resume integration (T034)
15. Persistence (T035)
16. Verify integration tests pass

**Week 4: Migration & Validation**
17. Agent iteration migration (T036)
18. Agent access migration (T037)
19. Unit tests (T038)
20. Full test suite (T039)
21. Quickstart validation (T040)
22. Final review and cleanup

---

**Total Tasks**: 40
**Parallel Tasks**: 23 (57.5%)
**Sequential Tasks**: 17 (42.5%)
**Estimated Effort**: 3-4 weeks with TDD approach
