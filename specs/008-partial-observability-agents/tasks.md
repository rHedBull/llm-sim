# Tasks: Partial Observability for Agents

**Input**: Design documents from `/specs/008-partial-observability-agents/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.12, Pydantic 2.x, pytest
2. Load design documents:
   → data-model.md: 5 new entities (ObservabilityLevel, VariableVisibilityConfig, ObservabilityEntry, DefaultObservability, ObservabilityConfig)
   → contracts/: 2 schema files (observability-config-schema.json, observation-format-schema.json)
   → research.md: 6 research decisions (noise model, observation structure, variable visibility, matrix storage, orchestrator integration, global state)
   → quickstart.md: 7 acceptance criteria
3. Generate tasks by category:
   → Setup: Dependencies already in pyproject.toml
   → Tests: 2 contract tests + 9 integration tests (from acceptance scenarios)
   → Core: 5 config models + observation construction + matrix lookup + filtering + noise
   → Integration: Orchestrator modification
   → Polish: Unit tests for each component
4. Apply TDD ordering: Tests before implementation
5. Mark [P] for parallel (different files)
6. Number tasks sequentially
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- Single project: `src/llm_sim/`, `tests/` at repository root
- All paths shown below are absolute from repository root

---

## Phase 3.1: Setup

- [x] **T001** Verify dependencies in pyproject.toml (Pydantic 2.x, PyYAML 6.x, structlog 24.x already present)

## Phase 3.2: Contract Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [x] **T002** [P] Contract test for observability configuration schema
  **File**: `tests/contract/test_observability_config_contract.py`
  **Content**:
  - Load `contracts/observability-config-schema.json`
  - Test valid configuration passes validation
  - Test missing `enabled` field rejected
  - Test missing `variable_visibility` rejected
  - Test missing `matrix` rejected
  - Test invalid observability level ("invalid_level") rejected
  - Test negative noise value rejected
  - Test overlapping external/internal variables rejected
  - **Expected**: All tests FAIL (ObservabilityConfig not yet implemented)

- [x] **T003** [P] Contract test for observation format schema
  **File**: `tests/contract/test_observation_format_contract.py`
  **Content**:
  - Load `contracts/observation-format-schema.json`
  - Test observation has same structure as SimulationState (turn, agents, global_state, reasoning_chains)
  - Test reasoning_chains is always empty list
  - Test agents dict can be subset of ground truth
  - Test agent state objects have same Pydantic model structure
  - **Expected**: All tests FAIL (construct_observation not yet implemented)

## Phase 3.3: Integration Tests from Acceptance Scenarios
**CRITICAL: Write these tests BEFORE implementing observation construction**

- [x] **T004** [P] Integration test: Agent receives filtered observations based on matrix
  **File**: `tests/integration/test_partial_observability.py::test_agent_receives_filtered_observations_based_on_matrix`
  **Content** (Acceptance Scenario 1):
  - Given: 3 agents with different observability levels configured
  - When: Agent1 requests current state
  - Then: Agent1 sees Agent2 (external) but not Agent3 (unaware)
  - **Expected**: FAIL (construct_observation not implemented)

- [x] **T005** [P] Integration test: External observer sees only public variables
  **File**: `tests/integration/test_partial_observability.py::test_external_observer_sees_only_public_variables`
  **Content** (Acceptance Scenario 2):
  - Given: Agent with external access to another agent
  - When: Observer requests observations
  - Then: Only external variables visible, internal hidden
  - **Expected**: FAIL (variable filtering not implemented)

- [x] **T006** [P] Integration test: Insider observer sees all variables
  **File**: `tests/integration/test_partial_observability.py::test_insider_observer_sees_all_variables`
  **Content** (Acceptance Scenario 3):
  - Given: Agent with insider access
  - When: Observer requests observations
  - Then: All variables visible with minimal noise
  - **Expected**: FAIL (insider filtering not implemented)

- [x] **T007** [P] Integration test: Unaware agent completely invisible
  **File**: `tests/integration/test_partial_observability.py::test_unaware_agent_completely_invisible`
  **Content** (Acceptance Scenario 4):
  - Given: Agent marked unaware of target
  - When: Observer requests observations
  - Then: Target not in observation.agents dict
  - **Expected**: FAIL (unaware filtering not implemented)

- [x] **T008** Integration test: Disabled observability provides full visibility  ✅
  **File**: `tests/integration/test_backward_compatibility.py::test_disabled_observability_provides_full_visibility`
  **Content** (Acceptance Scenario 5):
  - Given: observability.enabled = false
  - When: Agent requests observations
  - Then: Receives complete global state
  - **Status**: PASSING ✅

- [x] **T009** Integration test: Missing observability config provides full visibility  ✅
  **File**: `tests/integration/test_backward_compatibility.py::test_missing_observability_config_provides_full_visibility`
  **Content** (Acceptance Scenario 6):
  - Given: No observability section in config
  - When: Agent requests observations
  - Then: Receives complete global state
  - **Status**: PASSING ✅

- [x] **T010** [P] Integration test: Asymmetric visibility between agents
  **File**: `tests/integration/test_partial_observability.py::test_asymmetric_visibility_between_agents`
  **Content** (Acceptance Scenario 7):
  - Given: A sees B, B cannot see A
  - When: Each requests observations
  - Then: A's observation includes B, B's excludes A
  - **Expected**: FAIL (asymmetric matrix not implemented)

- [x] **T011** [P] Integration test: Undefined pairs use default observability
  **File**: `tests/integration/test_partial_observability.py::test_undefined_pairs_use_default_observability`
  **Content** (Acceptance Scenario 8):
  - Given: Default level = external with 0.1 noise
  - When: Agent observes undefined pair
  - Then: External variables with 0.1 noise applied
  - **Expected**: FAIL (default fallback not implemented)

- [x] **T012** [P] Integration test: Agent observes filtered global state
  **File**: `tests/integration/test_partial_observability.py::test_agent_observes_filtered_global_state`
  **Content** (Acceptance Scenario 9):
  - Given: Agent with external access to global state
  - When: Agent requests observations
  - Then: Only external global variables visible with noise
  - **Expected**: FAIL (global state observability not implemented)

---

## Phase 3.4: Core Implementation (ONLY after tests T002-T012 are failing)

### Configuration Models (can be done in parallel - different files)

- [x] **T013** [P] Implement ObservabilityLevel enum
  **File**: `src/llm_sim/infrastructure/observability/config.py` (NEW FILE)
  **Content**:
  ```python
  from enum import Enum

  class ObservabilityLevel(str, Enum):
      UNAWARE = "unaware"
      EXTERNAL = "external"
      INSIDER = "insider"
  ```
  - Import in `src/llm_sim/infrastructure/observability/__init__.py`
  - **Expected**: T002 still fails (need full ObservabilityConfig)

- [x] **T014** [P] Implement VariableVisibilityConfig model
  **File**: `src/llm_sim/infrastructure/observability/config.py`
  **Content**:
  - Pydantic model with `external: List[str]` and `internal: List[str]` fields
  - Validator: no overlap between lists
  - **Expected**: T002 still fails (need ObservabilityEntry)

- [x] **T015** [P] Implement ObservabilityEntry model
  **File**: `src/llm_sim/infrastructure/observability/config.py`
  **Content**:
  - Fields: observer (str), target (str), level (ObservabilityLevel), noise (float | None)
  - Validator: noise >= 0.0 if not None
  - **Expected**: T002 still fails (need DefaultObservability)

- [x] **T016** [P] Implement DefaultObservability model
  **File**: `src/llm_sim/infrastructure/observability/config.py`
  **Content**:
  - Fields: level (ObservabilityLevel), noise (float)
  - Validator: noise >= 0.0
  - **Expected**: T002 still fails (need full ObservabilityConfig with validation)

- [x] **T017** Implement ObservabilityConfig model with cross-validation
  **File**: `src/llm_sim/infrastructure/observability/config.py`
  **Content**:
  - Fields: enabled (bool), variable_visibility (VariableVisibilityConfig), matrix (List[ObservabilityEntry]), default (DefaultObservability | None)
  - Model validator: cross-reference agent names and variable names (requires ValidationInfo context)
  - Add to SimulationConfig in `src/llm_sim/models/config.py` as optional field
  - **Expected**: T002 contract tests START PASSING ✅

### Observability Matrix Lookup

- [x] **T018** [P] Implement ObservabilityMatrix class
  **File**: `src/llm_sim/infrastructure/observability/matrix.py` (NEW FILE)
  **Content**:
  - `__init__(entries: List[ObservabilityEntry], default: DefaultObservability)`
  - Build dict mapping (observer, target) → (level, noise)
  - `get_observability(observer: str, target: str) -> tuple[ObservabilityLevel, float]`
  - Return from dict or default if not found
  - **Expected**: No tests pass yet (matrix not used in observation construction)

### Deterministic Noise Generation

- [x] **T019** [P] Implement deterministic noise generation
  **File**: `src/llm_sim/infrastructure/observability/noise.py` (NEW FILE)
  **Content**:
  - `apply_noise(value: float, noise_factor: float, seed_components: tuple[int, str, str]) -> float`
  - If noise_factor == 0.0, return value unchanged
  - Create seed from hash(seed_components) where components = (turn, observer_id, variable_name)
  - Use `random.Random(seed)` for deterministic RNG
  - Apply multiplicative noise: `value * (1.0 + rng.uniform(-noise_factor, noise_factor))`
  - **Expected**: No tests pass yet (noise not integrated into observation construction)

### Variable Filtering Logic

- [x] **T020** Implement variable filtering  ✅
  **File**: `src/llm_sim/infrastructure/observability/filter.py` (NEW FILE)
  **Content**:
  - `filter_variables(state: BaseModel, level: ObservabilityLevel, visibility_config: VariableVisibilityConfig) -> Dict[str, Any]`
  - If level == UNAWARE: return empty dict (should not be called, but safe)
  - If level == EXTERNAL: return only variables in visibility_config.external
  - If level == INSIDER: return all variables (no filtering)
  - Return dict of {var_name: var_value}
  - **Expected**: No tests pass yet (filtering not integrated into observation construction)

### Observation Construction (Core Integration)

- [x] **T021** Implement construct_observation function
  **File**: `src/llm_sim/models/observation.py` (NEW FILE)
  **Content**:
  - `construct_observation(observer_id: str, ground_truth: SimulationState, config: ObservabilityConfig) -> SimulationState`
  - Initialize ObservabilityMatrix from config
  - Loop through ground_truth.agents:
    - Get (level, noise) from matrix.get_observability(observer_id, agent_id)
    - If level == UNAWARE: skip (don't add to filtered_agents)
    - Else: filter variables, apply noise, create new agent state instance
  - Filter and noise global_state based on matrix.get_observability(observer_id, "global")
  - Return new SimulationState with filtered agents, filtered global_state, empty reasoning_chains
  - **Expected**: T003-T012 integration tests START PASSING ✅

---

## Phase 3.5: Orchestrator Integration

- [x] **T022** Integrate observation construction into orchestrator turn loop
  **File**: `src/llm_sim/orchestrator.py` (MODIFY EXISTING)
  **Content**:
  - Import `construct_observation` from `llm_sim.models.observation`
  - In turn loop, before calling `agent.decide_action(current_state)`:
    ```python
    if self.config.observability and self.config.observability.enabled:
        observation = construct_observation(agent_name, current_state, self.config.observability)
    else:
        observation = current_state  # Full observability
    action = await agent.decide_action(observation)
    ```
  - Add structured logging: `logger.info("constructing_observation", observer=agent_name, turn=current_state.turn)`
  - **Expected**: T008, T009 backward compatibility tests START PASSING ✅

---

## Phase 3.6: Unit Tests for Components

- [x] **T023** Unit tests for ObservabilityMatrix lookup  ✅
  **File**: `tests/unit/test_observability_matrix.py` (NEW FILE)
  **Content**:
  - Test get_observability returns correct (level, noise) for defined pairs
  - Test get_observability returns default for undefined pairs
  - Test matrix handles "global" target correctly
  - Test matrix lookup is O(1) (performance)

- [x] **T024** Unit tests for deterministic noise generation  ✅
  **File**: `tests/unit/test_noise_generation.py`
  **Content**:
  - Test same seed produces same noise (determinism)
  - Test noise_factor=0.0 returns value unchanged
  - Test noise is bounded within [-noise_factor, +noise_factor] range
  - Test different seeds produce different noise values
  - Test multiplicative noise formula correct

- [x] **T025** Unit tests for variable filtering  ✅
  **File**: `tests/unit/test_observation_filter.py`
  **Content**:
  - Test EXTERNAL level filters to external variables only
  - Test INSIDER level returns all variables
  - Test UNAWARE level returns empty dict
  - Test filtering preserves variable types and values
  - Test variables not in external or internal lists default to external

---

## Phase 3.7: Quickstart Validation

- [x] **T026** Run quickstart scenario from quickstart.md  ✅
  **Manual Test**:
  - Created test_observability.yaml from quickstart.md template
  - Created test_quickstart.py validation script
  - Verified all 7+ acceptance criteria pass
  - Checked logs for observation construction events
  - **Status**: All quickstart criteria PASSING ✅

---

## Phase 3.8: Polish & Documentation

- [x] **T027** Add structured logging for observation construction  ✅
  **File**: `src/llm_sim/models/observation.py`
  **Content**:
  - Implemented logging for agent filtering (excluded vs included)
  - Implemented logging for noise application per variable
  - Implemented logging for global state filtering
  - Event names: `observation_construction_bypassed`, `observation_filtered.agents_filtered`, `observation_filtered.global_state_filtered`, `noise_applied`
  - **Status**: Logging complete and tested

- [x] **T028** Add validation error messages with context  ✅
  **File**: `src/llm_sim/infrastructure/observability/config.py`
  **Content**:
  - Enhanced error messages with context and remediation steps
  - Variable overlap validation with clear remediation
  - Noise validation with usage guidance
  - Matrix entry format validation with examples
  - **Status**: Validation messages complete

- [x] **T029** Performance test: Observation construction overhead  ✅
  **File**: `tests/integration/test_observability_performance.py`
  **Content**:
  - Tests observation construction for 100 agents with 20 variables each
  - Measures time per observation construction (< 10ms per agent)
  - Verifies memory overhead acceptable (< 1MB per observation)
  - **Status**: Performance tests PASSING ✅

- [x] **T030** Remove duplication in observation construction  ✅
  **Review**:
  - Refactored noise application into `_apply_noise_to_variables` helper
  - Centralized noise logic in noise.py
  - No duplication in filtering logic (single filter_variables function)
  - **Status**: Code duplication removed

---

## Dependencies

**Critical Path (must be sequential)**:
1. T001 (setup) blocks everything
2. T002-T012 (all tests) must be written and failing BEFORE T013-T021
3. T013-T017 (config models) before T021 (observation construction uses them)
4. T018 (matrix) before T021 (observation construction uses matrix)
5. T019 (noise) before T021 (observation construction applies noise)
6. T020 (filtering) before T021 (observation construction filters variables)
7. T021 (observation construction) before T022 (orchestrator integration)
8. T022 before T026 (quickstart needs integrated system)

**Parallel Opportunities**:
- T002-T012 can all run in parallel (different test files)
- T013-T016 can run in parallel (different config model classes in same file)
- T018, T019, T020 can run in parallel (different component files)
- T023-T025 can run in parallel (different unit test files)
- T027-T029 can run in parallel (different concerns)

---

## Parallel Execution Examples

### Phase 3.2-3.3: Write All Tests in Parallel
```bash
# Launch T002-T012 together (11 parallel tasks):
uv run claude-code "Contract test for observability configuration schema in tests/contract/test_observability_config_contract.py"
uv run claude-code "Contract test for observation format schema in tests/contract/test_observation_format_contract.py"
uv run claude-code "Integration test: Agent receives filtered observations in tests/integration/test_partial_observability.py::test_agent_receives_filtered_observations_based_on_matrix"
# ... (and so on for T004-T012)
```

### Phase 3.4: Implement Config Models in Parallel
```bash
# Launch T013-T016 together (4 parallel tasks):
uv run claude-code "Implement ObservabilityLevel enum in src/llm_sim/infrastructure/observability/config.py"
uv run claude-code "Implement VariableVisibilityConfig model in src/llm_sim/infrastructure/observability/config.py"
uv run claude-code "Implement ObservabilityEntry model in src/llm_sim/infrastructure/observability/config.py"
uv run claude-code "Implement DefaultObservability model in src/llm_sim/infrastructure/observability/config.py"
```

### Phase 3.4: Implement Core Components in Parallel
```bash
# Launch T018-T020 together (3 parallel tasks):
uv run claude-code "Implement ObservabilityMatrix class in src/llm_sim/infrastructure/observability/matrix.py"
uv run claude-code "Implement deterministic noise generation in src/llm_sim/infrastructure/observability/noise.py"
uv run claude-code "Implement variable filtering in src/llm_sim/infrastructure/observability/filter.py"
```

---

## Notes
- **TDD Discipline**: T002-T012 must all FAIL before starting T013
- **File Organization**: New `infrastructure/observability/` module keeps observability logic isolated
- **Backward Compatibility**: T008-T009 verify full observability when disabled/missing
- **Constitution Compliance**: Following Test-First (Principle 4), KISS (Principle 1), Clean Interfaces (Principle 5)
- **Deterministic Testing**: Noise generation uses seeded RNG for reproducible tests

---

## Task Count Summary
- Setup: 1 task (T001)
- Tests: 11 tasks (T002-T012) - All parallelizable
- Config Models: 5 tasks (T013-T017) - 4 parallelizable
- Core Components: 4 tasks (T018-T021) - 3 parallelizable
- Integration: 1 task (T022)
- Unit Tests: 3 tasks (T023-T025) - All parallelizable
- Validation: 1 task (T026)
- Polish: 4 tasks (T027-T030) - 3 parallelizable

**Total: 30 tasks**
**Parallelizable: 25 tasks (83%)**

---

## Validation Checklist

- [x] All contracts have corresponding tests (T002-T003)
- [x] All entities have model tasks (T013-T017 for 5 entities)
- [x] All tests come before implementation (T002-T012 before T013-T021)
- [x] Parallel tasks truly independent (checked file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task (verified)
- [x] All acceptance scenarios have integration tests (T004-T012 cover 9 scenarios)
- [x] TDD ordering enforced (tests must fail before implementation)

---

*Tasks ready for execution. Follow TDD strictly: Write tests → Verify failures → Implement → Tests pass*
