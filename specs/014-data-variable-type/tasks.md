# Tasks: Complex Data Type Support for State Variables

**Feature Branch**: `014-data-variable-type`
**Input**: Design documents from `/specs/014-data-variable-type/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/variable_definition.json

**Tests**: Tests are INCLUDED per Principle 4 (Test-First Development) from plan.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US6)
- Include exact file paths in descriptions

## Project Structure
Single project structure at repository root:
- `src/llm_sim/` - Source code
- `tests/` - Test files
- `examples/` - Example configurations

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Verify existing project dependencies (Pydantic 2.x, PyYAML 6.x, structlog 24.x, NetworkX 3.5) in pyproject.toml
- [X] T002 [P] Create new exception classes module at `src/llm_sim/models/exceptions.py` (ComplexTypeError, CircularSchemaError, DepthLimitError)
- [X] T003 [P] Create type helpers module at `src/llm_sim/utils/type_helpers.py` for type introspection utilities
- [X] T004 Create example config file at `examples/trading_simulation.yaml` (stub - will be filled in US5)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Extend `VariableDefinition` class in `src/llm_sim/models/config.py` to add new type enum values ("dict", "list", "tuple", "str", "object")
- [X] T006 Add complex type fields to `VariableDefinition` in `src/llm_sim/models/config.py` (key_type, value_type, item_type, item_types, schema, pattern, max_length)
- [X] T007 Implement type annotation generation helper in `src/llm_sim/utils/type_helpers.py` (get_type_annotation, introspect_type, unwrap_optional functions)
- [X] T008 Implement nesting depth validation in `src/llm_sim/utils/type_helpers.py` (check_nesting_depth function per research.md §3.1)
- [X] T009 Implement circular reference detection in `src/llm_sim/utils/type_helpers.py` (detect_schema_cycle function using DFS per research.md §2.1)
- [X] T010 Create validation error formatter in `src/llm_sim/models/exceptions.py` (loc_to_dot_notation, format_validation_error functions per research.md §1.5)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Define Dictionary Variables for Inventory Systems (Priority: P1) 🎯 MVP

**Goal**: Support dict type with dynamic keys (key_type + value_type) and fixed schema mode to enable inventory systems

**Independent Test**: Create YAML config with dict-typed inventory variable, initialize simulation, verify agent state contains dictionary with correct types

### Tests for User Story 1 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD - Red phase)**

- [X] T011 [P] [US1] Unit test for dict with dynamic keys in `tests/unit/test_variable_definition.py` (test_dict_dynamic_keys_validation)
- [X] T012 [P] [US1] Unit test for dict with fixed schema in `tests/unit/test_variable_definition.py` (test_dict_fixed_schema_validation)
- [X] T013 [P] [US1] Unit test for dict depth limits (4 levels) in `tests/unit/test_variable_definition.py` (test_dict_exceeds_depth_limit)
- [X] T014 [P] [US1] Unit test for dict collection size limit (1000 items) in `tests/unit/test_variable_definition.py` (test_dict_exceeds_size_limit)
- [X] T015 [P] [US1] Integration test for inventory dict in simulation in `tests/integration/test_complex_simulation.py` (test_inventory_dict_initialization_and_access)

**Verify**: All tests PASS ✓

### Implementation for User Story 1 (TDD - Green phase)

- [X] T016 [US1] Implement dict type validation logic in `VariableDefinition` in `src/llm_sim/models/config.py` (validate dict requires key_type+value_type OR schema)
- [X] T017 [US1] Implement dict type annotation generation in `src/llm_sim/models/state.py` (extend create_agent_state_model and create_global_state_model for dict)
- [X] T018 [US1] Add dict-specific Pydantic validation in `src/llm_sim/models/state.py` (RootModel for dynamic keys, nested model for schema mode per research.md §1.1)
- [X] T019 [US1] Implement depth validation for dict in `src/llm_sim/utils/type_helpers.py` (integrate check_nesting_depth with 4-level limit)
- [X] T020 [US1] Implement collection size validation for dict in `src/llm_sim/models/state.py` (Field with max_length=1000 per data-model.md)
- [X] T021 [US1] Add error formatting for dict validation errors in `src/llm_sim/models/exceptions.py` (ensure dot notation for nested dict keys)
- [X] T022 [US1] Update checkpoint serialization in `src/llm_sim/persistence/checkpoint_manager.py` to handle dict types (model_dump_json per research.md §4.1)

**Verify**: All User Story 1 tests now PASS ✓

### Refactor for User Story 1 (TDD - Refactor phase)

- [X] T023 [US1] Add logging for dict validation operations in relevant modules using structlog
- [X] T024 [US1] Performance optimization: Enable string caching for dict-heavy models in `src/llm_sim/models/state.py` (ConfigDict with cache_strings='keys' per research.md §5.1)

**Checkpoint**: ✅ At this point, dictionary variables (both dynamic and fixed schema) are fully functional and testable independently

---

## Phase 4: User Story 2 - Define Tuple Variables for Spatial Coordinates (Priority: P1)

**Goal**: Support tuple type with per-element type constraints to enable coordinate systems

**Independent Test**: Create config with tuple-typed location variable, verify type enforcement per element, test immutability

### Tests for User Story 2 ⚠️

- [X] T025 [P] [US2] Unit test for tuple with homogeneous types in `tests/unit/test_variable_definition.py` (test_tuple_homogeneous_validation)
- [X] T026 [P] [US2] Unit test for tuple with heterogeneous types in `tests/unit/test_variable_definition.py` (test_tuple_heterogeneous_validation)
- [X] T027 [P] [US2] Unit test for tuple per-element constraints in `tests/unit/test_variable_definition.py` (test_tuple_element_constraints_rgb)
- [X] T028 [P] [US2] Unit test for tuple length validation in `tests/unit/test_variable_definition.py` (test_tuple_length_mismatch_error)
- [X] T029 [P] [US2] Unit test for tuple immutability in `tests/unit/test_state_models.py` (test_tuple_immutability_preserved)
- [X] T030 [P] [US2] Integration test for coordinate tuple in simulation in `tests/integration/test_complex_simulation.py` (test_tuple_coordinates_in_simulation)

**Verify**: All tests FAIL before proceeding to implementation

### Implementation for User Story 2

- [X] T031 [US2] Implement tuple type validation logic in `VariableDefinition` in `src/llm_sim/models/config.py` (validate tuple requires item_types list)
- [X] T032 [US2] Implement tuple type annotation generation in `src/llm_sim/models/state.py` (tuple[Type1, Type2, ...] per research.md §1.3)
- [X] T033 [US2] Add tuple-specific Pydantic validation in `src/llm_sim/models/state.py` (fixed-length tuple with per-element type constraints)
- [X] T034 [US2] Implement per-element constraint validation for tuple in `src/llm_sim/models/state.py` (Annotated types with Field per research.md §1.3)
- [X] T035 [US2] Update checkpoint serialization to handle tuple → JSON array → tuple round-trip in `src/llm_sim/persistence/checkpoint_manager.py` (document behavior per research.md §4.1)
- [X] T036 [US2] Add error formatting for tuple validation errors in `src/llm_sim/models/exceptions.py` (include element index in path)

**Verify**: All User Story 2 tests now PASS

### Refactor for User Story 2

- [X] T037 [US2] Add logging for tuple validation operations

**Checkpoint**: At this point, tuple variables with per-element constraints should be fully functional

---

## Phase 5: User Story 3 - Define List Variables for History Tracking (Priority: P2)

**Goal**: Support list type with item type constraints and max_length to enable history tracking

**Independent Test**: Create config with list-typed history variable, add items, verify type checking, test length constraints

### Tests for User Story 3 ⚠️

- [X] T038 [P] [US3] Unit test for list with scalar item type in `tests/unit/test_variable_definition.py` (test_list_scalar_items)
- [X] T039 [P] [US3] Unit test for list with complex item type in `tests/unit/test_variable_definition.py` (test_list_complex_items_tuple)
- [X] T040 [P] [US3] Unit test for list max_length constraint in `tests/unit/test_variable_definition.py` (test_list_max_length_validation)
- [X] T041 [P] [US3] Unit test for list nesting depth (3 levels) in `tests/unit/test_variable_definition.py` (test_list_exceeds_depth_limit)
- [X] T042 [P] [US3] Unit test for list collection size limit (1000 items) in `tests/unit/test_variable_definition.py` (test_list_exceeds_size_limit)
- [X] T043 [P] [US3] Integration test for history list in simulation in `tests/integration/test_complex_simulation.py` (test_action_history_list_operations)

**Verify**: All tests PASS ✓

### Implementation for User Story 3

- [X] T044 [US3] Implement list type validation logic in `VariableDefinition` in `src/llm_sim/models/config.py` (validate list requires item_type)
- [X] T045 [US3] Implement list type annotation generation in `src/llm_sim/models/state.py` (list[ItemType] per research.md §1.2)
- [X] T046 [US3] Add list-specific Pydantic validation in `src/llm_sim/models/state.py` (Annotated[list[T], Field(max_length=...)] per research.md §1.2)
- [X] T047 [US3] Implement depth validation for list in `src/llm_sim/utils/type_helpers.py` (check_nesting_depth with 3-level limit)
- [X] T048 [US3] Implement collection size validation for list in `src/llm_sim/models/state.py` (max_length constraint, default 1000)
- [X] T049 [US3] Update checkpoint serialization to handle list types in `src/llm_sim/persistence/checkpoint_manager.py`
- [X] T050 [US3] Add error formatting for list validation errors in `src/llm_sim/models/exceptions.py` (include list index in path)

**Verify**: All User Story 3 tests now PASS ✓

### Refactor for User Story 3

- [X] T051 [US3] Add logging for list validation operations

**Checkpoint**: At this point, list variables with item type and length constraints should be fully functional

---

## Phase 6: User Story 4 - Define Unrestricted String Variables (Priority: P2)

**Goal**: Support unrestricted str type with optional pattern validation to enable dynamic string values

**Independent Test**: Create config with unrestricted string variables, test pattern validation, nullable behavior, and length constraints

### Tests for User Story 4 ⚠️

- [X] T052 [P] [US4] Unit test for unrestricted string in `tests/unit/test_variable_definition.py` (test_str_unrestricted_nullable)
- [X] T053 [P] [US4] Unit test for string with pattern validation in `tests/unit/test_variable_definition.py` (test_str_pattern_validation_regex)
- [X] T054 [P] [US4] Unit test for string with max_length in `tests/unit/test_variable_definition.py` (test_str_max_length_constraint)
- [X] T055 [P] [US4] Unit test for string pattern validation failure in `tests/unit/test_variable_definition.py` (test_str_pattern_mismatch_error)
- [X] T056 [P] [US4] Integration test for string variables in simulation in `tests/integration/test_complex_simulation.py` (test_destination_string_nullable)

**Verify**: All tests FAIL before proceeding to implementation

### Implementation for User Story 4

- [X] T057 [US4] Implement str type validation logic in `VariableDefinition` in `src/llm_sim/models/config.py` (validate str accepts pattern and max_length)
- [X] T058 [US4] Implement str type annotation generation in `src/llm_sim/models/state.py` (Optional[str] for nullable, str for required)
- [X] T059 [US4] Add str-specific Pydantic validation in `src/llm_sim/models/state.py` (Annotated[str, Field(pattern=..., max_length=...)] per research.md §1.6)
- [X] T060 [US4] Update checkpoint serialization to handle str types in `src/llm_sim/persistence/checkpoint_manager.py` (null handling per research.md §4.2)

**Verify**: All User Story 4 tests now PASS

### Refactor for User Story 4

- [X] T061 [US4] Add logging for string validation operations

**Checkpoint**: At this point, string variables with pattern and length validation should be fully functional

---

## Phase 7: User Story 5 - Define Nested Object Variables for Complex Entities (Priority: P3)

**Goal**: Support object type with nested schema definition to enable complex nested structures

**Independent Test**: Create config with deeply nested structures, verify validation at all levels, test serialization

### Tests for User Story 5 ⚠️

- [X] T062 [P] [US5] Unit test for object with nested schema in `tests/unit/test_variable_definition.py` (test_object_nested_schema_validation)
- [X] T063 [P] [US5] Unit test for object with mixed complex types in `tests/unit/test_variable_definition.py` (test_object_contains_dict_list_tuple)
- [X] T064 [P] [US5] Unit test for circular reference detection in `tests/unit/test_variable_definition.py` (test_circular_schema_error_with_path)
- [X] T065 [P] [US5] Unit test for deeply nested validation errors in `tests/unit/test_state_models.py` (test_nested_validation_error_path)
- [X] T066 [P] [US5] Integration test for nested town objects in simulation in `tests/integration/test_complex_simulation.py` (test_nested_town_global_state)
- [X] T067 [P] [US5] End-to-end test with full trading simulation config in `tests/integration/test_complex_simulation.py` (test_trading_simulation_complete)

**Verify**: All tests FAIL before proceeding to implementation

### Implementation for User Story 5

- [X] T068 [US5] Implement object type validation logic in `VariableDefinition` in `src/llm_sim/models/config.py` (validate object requires schema)
- [X] T069 [US5] Implement object type annotation generation in `src/llm_sim/models/state.py` (create_nested_model_from_schema function per research.md §1.4)
- [X] T070 [US5] Add object-specific Pydantic validation in `src/llm_sim/models/state.py` (recursive nested BaseModel generation)
- [X] T071 [US5] Integrate circular reference detection in config loading in `src/llm_sim/models/config.py` (call detect_schema_cycle during validation)
- [X] T072 [US5] Update checkpoint serialization to handle nested object types in `src/llm_sim/persistence/checkpoint_manager.py` (recursive model_dump_json)
- [X] T073 [US5] Add comprehensive error formatting for nested object validation in `src/llm_sim/models/exceptions.py` (full dot notation path per data-model.md)
- [X] T074 [US5] Complete example config file at `examples/trading_simulation.yaml` with all complex types demonstrated (inventory dicts, location tuples, town objects)

**Verify**: All User Story 5 tests now PASS

### Refactor for User Story 5

- [X] T075 [US5] Add logging for object validation operations with nested field paths

**Checkpoint**: All complex types (dict, list, tuple, str, object) should now be fully functional with nested structures

---

## Phase 8: User Story 6 - Migrate Existing Scalar-Only Simulation (Priority: P1)

**Goal**: Ensure backward compatibility - existing scalar-only simulations work without modification

**Independent Test**: Run existing test suite for scalar-only simulations against new version, verify all tests pass with no code changes

### Tests for User Story 6 ⚠️

- [X] T076 [P] [US6] Backward compatibility test for scalar-only config in `tests/integration/test_backward_compat.py` (test_existing_scalar_config_unchanged)
- [X] T077 [P] [US6] Backward compatibility test for old checkpoints in `tests/integration/test_backward_compat.py` (test_load_scalar_only_checkpoint)
- [X] T078 [P] [US6] Performance regression test for scalar-only simulation in `tests/performance/test_validation_perf.py` (test_scalar_only_performance_no_regression)

**Verify**: Tests should use existing scalar-only fixtures/configs and PASS without modification

### Implementation for User Story 6

- [X] T079 [US6] Verify no breaking changes to existing scalar type handling in `src/llm_sim/models/config.py` (float, int, bool, categorical unchanged)
- [X] T080 [US6] Verify checkpoint loading backward compatibility in `src/llm_sim/persistence/checkpoint_manager.py` (old scalar checkpoints load successfully)
- [X] T081 [US6] Performance benchmark comparison in `tests/performance/test_validation_perf.py` (< 5% difference per spec)

**Verify**: All backward compatibility tests PASS

**Checkpoint**: Existing simulations should work identically on the new version

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T082 [P] Add comprehensive docstrings to all new functions in `src/llm_sim/models/config.py`, `src/llm_sim/models/state.py`, `src/llm_sim/utils/type_helpers.py`
- [X] T083 [P] Create user guide section in project documentation referencing `specs/014-data-variable-type/quickstart.md`
- [X] T084 [P] Update CLAUDE.md to reflect new complex type capabilities
- [X] T085 Performance optimization: Implement model class caching by schema hash in `src/llm_sim/models/state.py` (per research.md §5.2)
- [X] T086 Memory monitoring: Add tracemalloc monitoring for validation operations in `src/llm_sim/models/state.py` (per research.md §5.3)
- [X] T087 Code cleanup: Refactor common validation patterns into reusable functions in `src/llm_sim/utils/type_helpers.py`
- [X] T088 Run full test suite with coverage report (target 90% for core, 80% for implementations per plan.md)
- [X] T089 Security review: Verify no injection vulnerabilities in pattern validation and schema parsing
- [X] T090 Run quickstart.md validation: Execute all examples from `specs/014-data-variable-type/quickstart.md` to verify accuracy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - **US1 (Dict)**: Independent - can start after Phase 2
  - **US2 (Tuple)**: Independent - can start after Phase 2 (parallel with US1)
  - **US3 (List)**: Independent - can start after Phase 2 (but uses dict/tuple in tests, so US1+US2 helpful)
  - **US4 (Str)**: Independent - can start after Phase 2 (parallel with US1, US2)
  - **US5 (Object)**: Depends on US1, US2, US3, US4 (uses all types in nested schemas)
  - **US6 (Backward Compat)**: Can test after any user story, but full validation needs all stories complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (Dict - P1)**: Can start after Foundational (Phase 2) - No dependencies
- **User Story 2 (Tuple - P1)**: Can start after Foundational (Phase 2) - No dependencies (parallel with US1)
- **User Story 3 (List - P2)**: Can start after Foundational (Phase 2) - Recommended after US1+US2 for nested list tests
- **User Story 4 (Str - P2)**: Can start after Foundational (Phase 2) - No dependencies (parallel with US1-3)
- **User Story 5 (Object - P3)**: Requires US1, US2, US3, US4 complete (uses all types in schemas)
- **User Story 6 (Backward Compat - P1)**: Can verify throughout, full test after all stories

### Within Each User Story (TDD Workflow)

1. **Red Phase**: Write tests FIRST, ensure they FAIL
2. **Green Phase**: Implement minimal code to make tests PASS
3. **Refactor Phase**: Clean up code, add logging, optimize
4. Dependencies within story:
   - Tests before implementation
   - Config validation before state model generation
   - State model generation before serialization
   - Core implementation before integration tests

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks marked [P] can run in parallel (T001, T002, T003)
- **Phase 2 (Foundational)**: Some parallelization possible (T005+T006 sequential, but T007+T008+T009+T010 can be parallel)
- **Phase 3-4 (US1 + US2)**: Can work on dict and tuple in parallel after Phase 2 completes
- **Phase 6 (US4)**: Can work on strings in parallel with US1, US2, US3
- **Within each user story**: All test tasks marked [P] can run in parallel
- **Phase 9 (Polish)**: Documentation tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Dictionary)

```bash
# Red phase - Write all tests in parallel:
Task: "[US1] Unit test for dict with dynamic keys"
Task: "[US1] Unit test for dict with fixed schema"
Task: "[US1] Unit test for dict depth limits"
Task: "[US1] Unit test for dict collection size limit"
Task: "[US1] Integration test for inventory dict"

# Verify all tests FAIL (Red phase complete)

# Green phase - Implement in sequence (some dependencies):
Task: "[US1] Implement dict type validation logic"
Task: "[US1] Implement dict type annotation generation"
Task: "[US1] Add dict-specific Pydantic validation"
# ... continue implementation tasks

# Verify all tests PASS (Green phase complete)

# Refactor phase:
Task: "[US1] Add logging for dict validation"
Task: "[US1] Performance optimization: string caching"

# Story complete - deploy/demo if desired
```

---

## Parallel Example: Foundational Phase

```bash
# After T005 and T006 (VariableDefinition extension) complete:
Task: "Implement type annotation generation helper" (T007)
Task: "Implement nesting depth validation" (T008)
Task: "Implement circular reference detection" (T009)
Task: "Create validation error formatter" (T010)
# All of these can run in parallel - different files
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only - Dict + Tuple)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dict)
4. Complete Phase 4: User Story 2 (Tuple)
5. **STOP and VALIDATE**: Test inventory + coordinates simulation independently
6. Deploy/demo MVP (trading agents with inventories and positions)

**MVP Scope**: Enables inventory systems and spatial simulations - the two most critical use cases per spec.md user story priorities.

### Incremental Delivery

1. **Foundation** (Phase 1-2) → Base infrastructure ready
2. **MVP** (US1 + US2) → Dict + Tuple support → Test independently → Deploy/Demo
3. **Expansion 1** (US3 + US4) → List + String support → Test independently → Deploy/Demo
4. **Expansion 2** (US5) → Nested objects → Test independently → Deploy/Demo
5. **Validation** (US6) → Backward compatibility confirmed → Deploy
6. **Polish** (Phase 9) → Documentation and optimization → Final release

Each increment adds value without breaking previous features.

### Parallel Team Strategy

With 3 developers:

1. **Team completes Setup + Foundational together** (Phase 1-2)
2. Once Foundational complete:
   - **Developer A**: User Story 1 (Dict)
   - **Developer B**: User Story 2 (Tuple)
   - **Developer C**: User Story 4 (Str) - independent track
3. After US1 + US2 complete:
   - **Developer A**: User Story 3 (List) - uses US1+US2
   - **Developer B**: User Story 6 (Backward Compat) - testing
   - **Developer C**: Continue US4 (Str)
4. After US1-4 complete:
   - **All Developers**: User Story 5 (Object) - uses all types
5. **All Developers**: Phase 9 (Polish) in parallel

---

## Performance & Quality Targets

**Per plan.md Technical Context:**

- **Validation Performance**: <10ms for 100 agents × 50 variables with 3 dicts, 2 lists, 1 tuple each
- **Test Coverage**: 90% for core (`src/llm_sim/models/`, `src/llm_sim/utils/`), 80% for implementations
- **Backward Compatibility**: <5% performance difference for scalar-only simulations
- **Collection Limits**: 1000 items max per dict/list, 4 levels max for dict nesting, 3 levels max for list nesting

**Quality Checkpoints:**

- Each user story must have independent test scenarios that PASS
- All tests must be written FIRST and FAIL before implementation (TDD Red-Green-Refactor)
- Validation error messages must include full dot-notation paths (e.g., "agent_state.inventory.food")
- Performance benchmarks must be run and meet targets before Phase 9

---

## Notes

- **[P]** tasks = different files, no dependencies - run in parallel
- **[Story]** label maps task to specific user story for traceability
- **TDD Required**: Write tests FIRST (Red), implement to pass (Green), then refactor
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Red phase validation)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Use `model_validate_json()` for performance (research.md §5.1)
- Enable string caching for dict-heavy models (research.md §5.1)
- Cache model classes by schema hash (research.md §5.2)

---

**Total Tasks**: 90 tasks across 9 phases
**Task Count per User Story**:
- US1 (Dict): 14 tasks (11 tests + implementation + 2 refactor)
- US2 (Tuple): 13 tasks (6 tests + implementation + 1 refactor)
- US3 (List): 14 tasks (6 tests + implementation + 1 refactor)
- US4 (Str): 10 tasks (5 tests + implementation + 1 refactor)
- US5 (Object): 14 tasks (6 tests + implementation + 1 refactor)
- US6 (Backward Compat): 6 tasks (3 tests + 3 verification)

**Parallel Opportunities**: ~30% of tasks can run in parallel with proper team coordination

**Suggested MVP Scope**: User Stories 1 + 2 (Dict + Tuple) = ~27 tasks including foundation

**Estimated Completion**:
- MVP (US1+US2): ~3-5 days for single developer
- Full Feature (All stories): ~7-10 days for single developer
- With 3 developers in parallel: ~3-5 days for full feature

---

*Generated*: 2025-10-13 | *Feature*: 014-data-variable-type | *Command*: /speckit.tasks
