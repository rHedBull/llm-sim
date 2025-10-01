# Tasks: Abstract Agent and Global State System

**Input**: Design documents from `/specs/007-we-want-to/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Single Python package structure:
- Source: `src/llm_sim/`
- Tests: `tests/` (unit/, integration/, contract/)
- Examples: `examples/`

---

## Phase 3.1: Setup & Infrastructure

- [X] **T001** Create test directory structure
  - Create: `tests/contract/`, `tests/unit/`, `tests/integration/`
  - Verify: Directories exist and have `__init__.py` files

- [X] **T002** [P] Add schema validation dependencies
  - Update: `pyproject.toml` or `requirements.txt`
  - Add: `jsonschema` library for contract validation
  - Verify: Can import `jsonschema`

- [X] **T003** [P] Create custom exception types
  - Create: `src/llm_sim/models/exceptions.py`
  - Add: `ConfigValidationError`, `SchemaCompatibilityError`
  - Verify: Exceptions inherit from appropriate base classes

---

## Phase 3.2: Contract Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [ ] **T004** [P] Contract test for config schema validation
  - Create: `tests/contract/test_config_schema.py`
  - Test: Valid config with state_variables passes
  - Test: Invalid type rejected
  - Test: Categorical without values rejected
  - Test: Min > max rejected
  - Test: Default outside min/max rejected
  - Read: `specs/007-we-want-to/contracts/config-schema.json`
  - Read: `specs/007-we-want-to/contracts/README.md` for examples
  - Verify: All tests FAIL (schema validation not implemented yet)

- [ ] **T005** [P] Contract test for checkpoint schema validation
  - Create: `tests/contract/test_checkpoint_schema.py`
  - Test: Valid checkpoint with schema_hash passes
  - Test: Missing schema_hash rejected
  - Test: Invalid schema_hash format rejected
  - Read: `specs/007-we-want-to/contracts/checkpoint-schema.json`
  - Verify: All tests FAIL (checkpoint schema not implemented yet)

---

## Phase 3.3: Unit Tests for Variable System (TDD) ⚠️ MUST COMPLETE BEFORE 3.4

- [ ] **T006** [P] Unit test for VariableDefinition validation
  - Create: `tests/unit/test_variable_definition.py`
  - Test: Float with min/max validates correctly
  - Test: Int with constraints validates correctly
  - Test: Bool with default validates correctly
  - Test: Categorical with values validates correctly
  - Test: Invalid type raises error
  - Test: Min > max raises error
  - Test: Default outside bounds raises error
  - Test: Categorical default not in values raises error
  - Read: `specs/007-we-want-to/data-model.md` (VariableDefinition section)
  - Verify: All tests FAIL (model not implemented yet)

- [ ] **T007** [P] Unit test for dynamic AgentState model creation
  - Create: `tests/unit/test_agent_state_factory.py`
  - Test: Create model with float variable
  - Test: Create model with int variable + constraints
  - Test: Create model with bool variable
  - Test: Create model with categorical variable
  - Test: Model has 'name' field (required)
  - Test: Model is frozen (immutable)
  - Test: Constraint violation on creation raises ValidationError
  - Read: `specs/007-we-want-to/data-model.md` (AgentState section)
  - Verify: All tests FAIL (factory function not implemented yet)

- [ ] **T008** [P] Unit test for dynamic GlobalState model creation
  - Create: `tests/unit/test_global_state_factory.py`
  - Test: Create model with mixed variable types
  - Test: Model is frozen (immutable)
  - Test: All fields have correct types
  - Test: Constraint enforcement works
  - Read: `specs/007-we-want-to/data-model.md` (GlobalState section)
  - Verify: All tests FAIL (factory function not implemented yet)

- [ ] **T009** [P] Unit test for state updates with validation
  - Create: `tests/unit/test_state_updates.py`
  - Test: Valid update via model_copy() succeeds
  - Test: Update violating min constraint rejected
  - Test: Update violating max constraint rejected
  - Test: Invalid categorical value rejected
  - Test: Type mismatch rejected
  - Read: `specs/007-we-want-to/research.md` (Constraint Enforcement section)
  - Verify: All tests FAIL (validation not implemented yet)

- [ ] **T010** [P] Unit test for schema hash computation
  - Create: `tests/unit/test_schema_hash.py`
  - Test: Hash is deterministic (same input → same hash)
  - Test: Hash is order-independent (sorted keys)
  - Test: Different schemas produce different hashes
  - Test: Hash format is 64-char hex (SHA-256)
  - Read: `specs/007-we-want-to/data-model.md` (CheckpointMetadata section)
  - Verify: All tests FAIL (hash function not implemented yet)

- [ ] **T011** [P] Unit test for backward compatibility defaults
  - Create: `tests/unit/test_backward_compatibility.py`
  - Test: Config without state_variables uses defaults
  - Test: Default agent vars include 'economic_strength'
  - Test: Default global vars include legacy fields
  - Test: Deprecation warning is logged
  - Read: `specs/007-we-want-to/data-model.md` (SimulationConfig section)
  - Verify: All tests FAIL (defaults not implemented yet)

---

## Phase 3.4: Integration Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.5

- [ ] **T012** [P] Integration test: Custom agent variables (Acceptance Scenario 1)
  - Create: `tests/integration/test_custom_agent_variables.py`
  - Test: Load config with agent vars (gdp: float, population: int)
  - Test: Initialize simulation
  - Test: Agent states have custom variables with correct types
  - Test: No hardcoded 'economic_strength' field present
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS (integration not implemented yet)

- [ ] **T013** [P] Integration test: Custom global variables (Acceptance Scenario 2)
  - Create: `tests/integration/test_custom_global_variables.py`
  - Test: Load config with global vars (inflation: float, open_economy: bool)
  - Test: Initialize simulation
  - Test: Global state has custom variables
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

- [ ] **T014** [P] Integration test: Checkpoint persistence (Acceptance Scenario 3)
  - Create: `tests/integration/test_checkpoint_custom_vars.py`
  - Test: Run simulation with custom variables
  - Test: Create checkpoint
  - Test: Checkpoint contains all custom agent variables
  - Test: Checkpoint contains all custom global variables
  - Test: Checkpoint metadata includes schema_hash
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

- [ ] **T015** [P] Integration test: Multiple simulation types (Acceptance Scenario 4)
  - Create: `tests/integration/test_multiple_sim_types.py`
  - Test: Run economic simulation with econ variables
  - Test: Run military simulation with military variables
  - Test: Each tracks only its configured variables
  - Test: No variable bleeding between simulations
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

- [ ] **T016** [P] Integration test: Constraint enforcement (Acceptance Scenario 5)
  - Create: `tests/integration/test_constraint_enforcement.py`
  - Test: Define variable with min/max constraints
  - Test: Attempt update exceeding max
  - Test: System rejects or clamps value
  - Test: Error message is clear
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

- [ ] **T017** [P] Integration test: Invalid config type (Acceptance Scenario 7)
  - Create: `tests/integration/test_invalid_config_type.py`
  - Test: Create config with unsupported type (e.g., complex_number)
  - Test: Load config
  - Test: System fails with validation error
  - Test: Error lists supported types
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

- [ ] **T018** [P] Integration test: Schema compatibility (Acceptance Scenario 6)
  - Create: `tests/integration/test_schema_compatibility.py`
  - Test: Save checkpoint with schema X
  - Test: Modify config to schema Y
  - Test: Attempt to load checkpoint
  - Test: System rejects with SchemaCompatibilityError
  - Test: Error message explains mismatch
  - Read: `specs/007-we-want-to/spec.md` (Acceptance Scenarios section)
  - Verify: Test FAILS

---

## Phase 3.5: Core Implementation (ONLY after tests 3.2-3.4 are failing)

### 3.5.1: Config Models

- [ ] **T019** Implement VariableDefinition model
  - Modify: `src/llm_sim/models/config.py`
  - Add: `VariableDefinition` Pydantic model
  - Add: Field validators for type, min/max, values, default
  - Add: Cross-field validation (default in bounds, etc.)
  - Read: `specs/007-we-want-to/data-model.md` (VariableDefinition section)
  - Verify: T006 tests pass

- [ ] **T020** Implement StateVariablesConfig model
  - Modify: `src/llm_sim/models/config.py`
  - Add: `StateVariablesConfig` Pydantic model
  - Add: `agent_vars` and `global_vars` dict fields
  - Add: Validation for variable name conflicts
  - Read: `specs/007-we-want-to/data-model.md` (StateVariablesConfig section)
  - Verify: T004 contract tests pass

- [ ] **T021** Extend SimulationConfig with state_variables
  - Modify: `src/llm_sim/models/config.py`
  - Add: `state_variables: Optional[StateVariablesConfig]` field
  - Add: Backward compatibility defaults logic
  - Add: Deprecation warning when state_variables is None
  - Read: `specs/007-we-want-to/data-model.md` (SimulationConfig section)
  - Verify: T011 backward compatibility tests pass

### 3.5.2: Dynamic State Models

- [ ] **T022** Implement create_agent_state_model() factory
  - Modify: `src/llm_sim/models/state.py`
  - Add: `create_agent_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]`
  - Implement: Dynamic field generation for each variable type
  - Implement: Field constraints (ge, le, Literal)
  - Implement: Frozen config
  - Read: `specs/007-we-want-to/data-model.md` (AgentState section)
  - Read: `specs/007-we-want-to/research.md` (Pydantic Dynamic Model Creation)
  - Verify: T007 tests pass

- [ ] **T023** Implement create_global_state_model() factory
  - Modify: `src/llm_sim/models/state.py`
  - Add: `create_global_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]`
  - Implement: Same logic as T022 but no 'name' field
  - Read: `specs/007-we-want-to/data-model.md` (GlobalState section)
  - Verify: T008 tests pass

- [ ] **T024** Remove hardcoded AgentState and GlobalState classes
  - Modify: `src/llm_sim/models/state.py`
  - Remove: Old static `class AgentState` definition
  - Remove: Old static `class GlobalState` definition
  - Keep: `SimulationState` class (structure unchanged)
  - Update: Any imports/references to use factory functions
  - Verify: T007, T008 tests still pass
  - Verify: T009 state update tests pass

### 3.5.3: Checkpoint Schema Validation

- [ ] **T025** Implement compute_schema_hash() function
  - Create: `src/llm_sim/persistence/schema_hash.py` (new file)
  - Add: `compute_schema_hash(agent_vars, global_vars) -> str`
  - Implement: Deterministic, order-independent hash computation
  - Implement: SHA-256 with 64-char hex output
  - Read: `specs/007-we-want-to/data-model.md` (CheckpointMetadata section)
  - Read: `specs/007-we-want-to/research.md` (Checkpoint Schema Compatibility)
  - Verify: T010 schema hash tests pass

- [ ] **T026** Add schema_hash to CheckpointMetadata
  - Modify: `src/llm_sim/models/checkpoint.py`
  - Add: `schema_hash: str` field to CheckpointMetadata
  - Add: Field validator for 64-char hex format
  - Read: `specs/007-we-want-to/data-model.md` (CheckpointMetadata section)
  - Verify: T005 checkpoint contract tests pass

- [ ] **T027** Implement checkpoint save with schema_hash
  - Modify: `src/llm_sim/persistence/checkpoint_manager.py`
  - Update: Save method to compute and include schema_hash
  - Import: `compute_schema_hash` from schema_hash.py
  - Update: Checkpoint metadata creation
  - Verify: T014 checkpoint persistence integration test passes (save part)

- [ ] **T028** Implement checkpoint load with schema validation
  - Modify: `src/llm_sim/persistence/checkpoint_manager.py`
  - Update: Load method to validate schema_hash
  - Add: Compare checkpoint schema_hash with current config
  - Raise: `SchemaCompatibilityError` on mismatch
  - Add: Clear error message with hash values
  - Read: `specs/007-we-want-to/research.md` (Checkpoint Schema Compatibility)
  - Verify: T018 schema compatibility integration test passes
  - Verify: T014 checkpoint persistence integration test passes (load part)

### 3.5.4: Orchestrator Integration

- [ ] **T029** Update orchestrator to use dynamic state models
  - Modify: `src/llm_sim/orchestrator.py`
  - Update: Simulation initialization to call factory functions
  - Update: Create AgentState instances from dynamic model
  - Update: Create GlobalState instance from dynamic model
  - Update: Pass variable definitions to factory functions
  - Read: `specs/007-we-want-to/plan.md` (Project Structure section)
  - Verify: T012, T013 integration tests pass

- [ ] **T030** Ensure engines work with dynamic state
  - Check: `src/llm_sim/implementations/engines/*.py`
  - Update: Any code that assumes hardcoded fields
  - Update: Access state via attribute access (not dict keys)
  - Test: Existing economic engine still works
  - Verify: T015 multiple simulation types test passes

---

## Phase 3.6: Examples & Documentation

- [ ] **T031** [P] Create military simulation example config
  - Create: `examples/military_simulation.yaml`
  - Content: From `specs/007-we-want-to/quickstart.md` Step 1
  - Variables: tech_level, army_size, owned_regions (agent)
  - Variables: world_peace, total_casualties, dominant_tech (global)
  - Verify: Config loads without errors

- [ ] **T032** [P] Update existing economic example with state_variables
  - Modify: `examples/basic_economic.yaml`
  - Add: `state_variables` section
  - Define: economic_strength as float variable
  - Define: legacy global variables explicitly
  - Verify: Config loads and simulation runs

- [ ] **T033** [P] Create quickstart test script
  - Create: `tests/acceptance/test_quickstart_military_sim.py`
  - Implement: Automated version of quickstart.md steps
  - Test: Load military config
  - Test: Run simulation for 10 turns
  - Test: Verify checkpoint contains custom variables
  - Test: Verify schema_hash present
  - Read: `specs/007-we-want-to/quickstart.md`
  - Verify: Test passes end-to-end

---

## Phase 3.7: Polish & Validation

- [ ] **T034** [P] Add unit tests for edge cases
  - Create: `tests/unit/test_edge_cases.py`
  - Test: Empty agent_vars dict
  - Test: Empty global_vars dict
  - Test: Variable name with reserved keyword
  - Test: Very large min/max values
  - Test: Categorical with single value
  - Test: Unicode in categorical values
  - Verify: All edge cases handled gracefully

- [ ] **T035** [P] Performance test for large variable sets
  - Create: `tests/performance/test_variable_performance.py`
  - Test: Config load with 50 variables < 100ms
  - Test: State creation with 50 variables < 50ms
  - Test: Checkpoint save with 100 agents < 500ms
  - Test: Schema hash computation < 10ms
  - Read: `specs/007-we-want-to/plan.md` (Performance Goals)
  - Verify: All performance targets met

- [ ] **T036** [P] Add docstrings and type hints
  - Update: All new functions in state.py, config.py, schema_hash.py
  - Add: Comprehensive docstrings with examples
  - Add: Type hints for all parameters and return values
  - Verify: mypy passes with no errors

- [ ] **T037** Run full test suite and verify coverage
  - Run: `pytest tests/` (all tests)
  - Run: `pytest --cov=src/llm_sim tests/`
  - Target: >90% coverage for new code
  - Verify: All 7 acceptance scenarios pass
  - Verify: All contract tests pass
  - Verify: All unit tests pass
  - Verify: All integration tests pass

- [ ] **T038** Manual testing with quickstart guide
  - Follow: `specs/007-we-want-to/quickstart.md` exactly
  - Create: military_simulation.yaml manually
  - Run: Simulation and inspect output
  - Test: All validation scenarios (invalid type, constraint violation, schema mismatch)
  - Document: Any issues or unclear instructions
  - Verify: Quickstart is accurate and complete

- [ ] **T039** Code cleanup and refactoring
  - Review: All modified files for duplication
  - Refactor: Common validation logic into helpers
  - Remove: Dead code or unused imports
  - Format: Run `black` and `ruff check .`
  - Verify: Linters pass, tests still pass

---

## Dependencies

### Setup → Tests
- T001-T003 must complete before any test tasks

### Tests → Implementation
- T004-T018 (all tests) MUST complete before T019-T030 (implementation)
- Tests must FAIL before implementing

### Implementation Order
- T019-T021 (config models) → T022-T024 (state models)
- T025-T026 (schema hash) → T027-T028 (checkpoint integration)
- T019-T028 → T029-T030 (orchestrator integration)

### Examples & Docs
- T029-T030 → T031-T033 (examples need working implementation)

### Polish
- T019-T033 → T034-T039 (polish comes last)

### Specific Blockers
- T020 requires T019 (StateVariablesConfig uses VariableDefinition)
- T022, T023 require T019 (factories use VariableDefinition)
- T024 requires T022, T023 (remove old classes after factories work)
- T027 requires T025 (checkpoint save uses schema_hash function)
- T028 requires T026, T027 (load validates against saved hash)
- T029 requires T022, T023 (orchestrator uses factories)
- T033 requires T031 (quickstart test uses military config)
- T037 requires T001-T036 (final validation)

---

## Parallel Execution Examples

### Batch 1: Setup (all parallel)
```bash
# Run together:
Task: "Create test directory structure" (T001)
Task: "Add schema validation dependencies" (T002)
Task: "Create custom exception types" (T003)
```

### Batch 2: Contract Tests (all parallel)
```bash
# Run together after Batch 1:
Task: "Contract test for config schema validation in tests/contract/test_config_schema.py" (T004)
Task: "Contract test for checkpoint schema validation in tests/contract/test_checkpoint_schema.py" (T005)
```

### Batch 3: Unit Tests (all parallel)
```bash
# Run together after Batch 2:
Task: "Unit test for VariableDefinition validation in tests/unit/test_variable_definition.py" (T006)
Task: "Unit test for dynamic AgentState model creation in tests/unit/test_agent_state_factory.py" (T007)
Task: "Unit test for dynamic GlobalState model creation in tests/unit/test_global_state_factory.py" (T008)
Task: "Unit test for state updates with validation in tests/unit/test_state_updates.py" (T009)
Task: "Unit test for schema hash computation in tests/unit/test_schema_hash.py" (T010)
Task: "Unit test for backward compatibility defaults in tests/unit/test_backward_compatibility.py" (T011)
```

### Batch 4: Integration Tests (all parallel)
```bash
# Run together after Batch 3:
Task: "Integration test: Custom agent variables in tests/integration/test_custom_agent_variables.py" (T012)
Task: "Integration test: Custom global variables in tests/integration/test_custom_global_variables.py" (T013)
Task: "Integration test: Checkpoint persistence in tests/integration/test_checkpoint_custom_vars.py" (T014)
Task: "Integration test: Multiple simulation types in tests/integration/test_multiple_sim_types.py" (T015)
Task: "Integration test: Constraint enforcement in tests/integration/test_constraint_enforcement.py" (T016)
Task: "Integration test: Invalid config type in tests/integration/test_invalid_config_type.py" (T017)
Task: "Integration test: Schema compatibility in tests/integration/test_schema_compatibility.py" (T018)
```

### Batch 5: Config Models (sequential - same file)
```bash
# Run in order (modify same file):
Task: "Implement VariableDefinition model in src/llm_sim/models/config.py" (T019)
Task: "Implement StateVariablesConfig model in src/llm_sim/models/config.py" (T020)
Task: "Extend SimulationConfig with state_variables in src/llm_sim/models/config.py" (T021)
```

### Batch 6: State Models (sequential - same file)
```bash
# Run in order (modify same file):
Task: "Implement create_agent_state_model() factory in src/llm_sim/models/state.py" (T022)
Task: "Implement create_global_state_model() factory in src/llm_sim/models/state.py" (T023)
Task: "Remove hardcoded AgentState and GlobalState classes in src/llm_sim/models/state.py" (T024)
```

### Batch 7: Checkpoint Schema (T025 first, then T026 parallel-ish)
```bash
# T025 first:
Task: "Implement compute_schema_hash() function in src/llm_sim/persistence/schema_hash.py" (T025)

# Then T026 (different file):
Task: "Add schema_hash to CheckpointMetadata in src/llm_sim/models/checkpoint.py" (T026)
```

### Batch 8: Checkpoint Integration (sequential - same file)
```bash
# Run in order (modify same file):
Task: "Implement checkpoint save with schema_hash in src/llm_sim/persistence/checkpoint_manager.py" (T027)
Task: "Implement checkpoint load with schema validation in src/llm_sim/persistence/checkpoint_manager.py" (T028)
```

### Batch 9: Orchestrator (sequential - orchestrator depends on engines)
```bash
# Run in order:
Task: "Update orchestrator to use dynamic state models in src/llm_sim/orchestrator.py" (T029)
Task: "Ensure engines work with dynamic state in src/llm_sim/implementations/engines/*.py" (T030)
```

### Batch 10: Examples (all parallel)
```bash
# Run together after Batch 9:
Task: "Create military simulation example config in examples/military_simulation.yaml" (T031)
Task: "Update existing economic example with state_variables in examples/basic_economic.yaml" (T032)
Task: "Create quickstart test script in tests/acceptance/test_quickstart_military_sim.py" (T033)
```

### Batch 11: Polish (all parallel where possible)
```bash
# Run together after Batch 10:
Task: "Add unit tests for edge cases in tests/unit/test_edge_cases.py" (T034)
Task: "Performance test for large variable sets in tests/performance/test_variable_performance.py" (T035)
Task: "Add docstrings and type hints" (T036)
# Then sequential:
Task: "Run full test suite and verify coverage" (T037)
Task: "Manual testing with quickstart guide" (T038)
Task: "Code cleanup and refactoring" (T039)
```

---

## Validation Checklist

*GATE: Checked before marking feature complete*

- [x] All contracts have corresponding tests (T004, T005)
- [x] All entities have model tasks (T019-T024)
- [x] All 7 acceptance scenarios have integration tests (T012-T018)
- [x] All tests come before implementation (Phase 3.2-3.4 before 3.5)
- [x] Parallel tasks truly independent (verified - different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Backward compatibility tested (T011, T032)
- [x] Performance goals tested (T035)
- [x] Quickstart validated (T033, T038)

---

## Notes

### TDD Discipline
- **CRITICAL**: Do NOT implement T019-T030 until T004-T018 are written and failing
- Each implementation task should make specific tests pass
- Run tests after each implementation task

### Commit Strategy
- Commit after each test batch passes
- Commit message format: "feat: [Task ID] - [Description]"
- Example: "feat: T022 - Implement create_agent_state_model() factory"

### Avoiding Common Pitfalls
- Don't modify `config.py` in parallel (T019-T021 are sequential)
- Don't modify `state.py` in parallel (T022-T024 are sequential)
- Don't modify `checkpoint_manager.py` in parallel (T027-T028 are sequential)
- Verify tests fail before implementing (TDD discipline)
- Don't skip backward compatibility testing (T011, T032)

### Code Review Checkpoints
- After Phase 3.2-3.4: Review all tests for completeness
- After T024: Review state model implementation
- After T028: Review checkpoint integration
- After T030: Review orchestrator changes
- After T037: Final review before merge

---

*Tasks generated from plan.md, data-model.md, contracts/, and quickstart.md*
*Total: 39 tasks across 7 phases*
*Estimated parallel batches: 11 (with proper dependency management)*
