# Tasks: Separate Simulation Infrastructure from Domain Implementations

**Input**: Design documents from `/home/hendrik/coding/llm_sim/llm_sim/specs/005-we-want-to/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow
```
1. Load plan.md → Extract tech stack (Python 3.12, pytest)
2. Load data-model.md → Extract directory structure entities
3. Load contracts/ → Generate contract test tasks
4. Generate tasks by category:
   → Setup: directory structure
   → Tests: contract tests, discovery tests (TDD)
   → Migration: move files with import updates
   → Discovery: implement ComponentDiscovery
   → Integration: update orchestrator, tests
   → Documentation: pattern docs, migration guide
5. Apply task rules: Different files = [P], same file = sequential
6. Order by dependencies: Setup → Tests → Implementation → Integration
7. Validation: All contracts tested, TDD order preserved
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All paths are absolute from repository root

## Phase 3.1: Setup & Directory Structure

- [x] **T001** Create `src/llm_sim/infrastructure/` directory structure
  - Create `src/llm_sim/infrastructure/__init__.py`
  - Create `src/llm_sim/infrastructure/base/` directory
  - Create `src/llm_sim/infrastructure/base/__init__.py`
  - Create `src/llm_sim/infrastructure/patterns/` directory
  - Create `src/llm_sim/infrastructure/patterns/__init__.py`

- [x] **T002** Create `src/llm_sim/implementations/` directory structure
  - Create `src/llm_sim/implementations/__init__.py`
  - Create `src/llm_sim/implementations/agents/` directory with `__init__.py`
  - Create `src/llm_sim/implementations/engines/` directory with `__init__.py`
  - Create `src/llm_sim/implementations/validators/` directory with `__init__.py`

- [x] **T003** Create `docs/patterns/` directory for pattern documentation
  - Create `docs/` directory if not exists
  - Create `docs/patterns/` directory
  - Create empty placeholder files for pattern docs

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [x] **T004 [P]** Contract test for BaseAgent interface in `tests/contract/test_base_agent_contract.py`
  - Test BaseAgent is abstract (cannot instantiate)
  - Test decide_action is abstract method
  - Test receive_state default implementation
  - Test get_current_state returns None initially
  - Test concrete implementation can be instantiated
  - Must reference `llm_sim.infrastructure.base.agent.BaseAgent`

- [x] **T005 [P]** Contract test for BaseEngine interface in `tests/contract/test_base_engine_contract.py`
  - Test BaseEngine is abstract
  - Test all abstract methods (initialize_state, apply_actions, apply_engine_rules, check_termination)
  - Test run_turn method
  - Must reference `llm_sim.infrastructure.base.engine.BaseEngine`

- [x] **T006 [P]** Contract test for BaseValidator interface in `tests/contract/test_base_validator_contract.py`
  - Test BaseValidator is abstract
  - Test validate_action abstract method
  - Test validate_actions default implementation
  - Test get_stats method
  - Must reference `llm_sim.infrastructure.base.validator.BaseValidator`

- [x] **T007 [P]** Contract test for LLMAgent pattern in `tests/contract/test_llm_agent_contract.py`
  - Test LLMAgent extends BaseAgent
  - Test _construct_prompt abstract method
  - Test _validate_decision abstract method
  - Test decide_action implementation
  - Must reference `llm_sim.infrastructure.patterns.llm_agent.LLMAgent`

- [x] **T008 [P]** Contract test for LLMEngine pattern in `tests/contract/test_llm_engine_contract.py`
  - Test LLMEngine extends BaseEngine
  - Test _construct_state_update_prompt abstract method
  - Test _apply_state_update abstract method
  - Test run_turn implementation
  - Must reference `llm_sim.infrastructure.patterns.llm_engine.LLMEngine`

- [x] **T009 [P]** Contract test for LLMValidator pattern in `tests/contract/test_llm_validator_contract.py`
  - Test LLMValidator extends BaseValidator
  - Test _construct_validation_prompt abstract method
  - Test _get_domain_description abstract method
  - Test validate_actions implementation
  - Must reference `llm_sim.infrastructure.patterns.llm_validator.LLMValidator`

- [x] **T010 [P]** Unit tests for ComponentDiscovery in `tests/unit/test_component_discovery.py`
  - Test _filename_to_classname conversion (snake_case → PascalCase)
  - Test load_agent with valid implementation
  - Test load_agent with missing file (FileNotFoundError)
  - Test load_agent with invalid inheritance (TypeError)
  - Test load_agent with wrong class name (AttributeError)
  - Test caching behavior
  - Test list_agents returns available implementations
  - Test same for load_engine, load_validator

- [x] **T011 [P]** Integration test for reorganized structure in `tests/integration/test_reorganized_simulation.py`
  - Test simulation runs with new import paths
  - Test mixed agent types (BaseAgent and LLMAgent extensions)
  - Test orchestrator discovers implementations correctly
  - Test YAML config with filename references works

- [x] **T012 [P]** Integration test for backward compatibility in `tests/integration/test_backward_compatibility.py`
  - Test existing YAML configs still work
  - Test no breaking changes to orchestrator API
  - Test simulation produces same results as before reorganization

## Phase 3.3: Core Migration (ONLY after tests are failing)

### Move Abstract Base Classes

- [x] **T013 [P]** Move BaseAgent to `src/llm_sim/infrastructure/base/agent.py`
  - Copy `src/llm_sim/agents/base.py` → `src/llm_sim/infrastructure/base/agent.py`
  - Update imports in new location (if any internal imports)
  - Keep original file for now (will delete later)

- [x] **T014 [P]** Move BaseEngine to `src/llm_sim/infrastructure/base/engine.py`
  - Copy `src/llm_sim/engines/base.py` → `src/llm_sim/infrastructure/base/engine.py`
  - Update imports in new location
  - Keep original file for now

- [x] **T015 [P]** Move BaseValidator to `src/llm_sim/infrastructure/base/validator.py`
  - Copy `src/llm_sim/validators/base.py` → `src/llm_sim/infrastructure/base/validator.py`
  - Update imports in new location
  - Keep original file for now

### Move LLM Pattern Classes

- [x] **T016 [P]** Move LLMAgent to `src/llm_sim/infrastructure/patterns/llm_agent.py`
  - Copy `src/llm_sim/agents/llm_agent.py` → `src/llm_sim/infrastructure/patterns/llm_agent.py`
  - Update import: `from llm_sim.agents.base import BaseAgent` → `from llm_sim.infrastructure.base.agent import BaseAgent`
  - Keep original file for now

- [x] **T017 [P]** Move LLMEngine to `src/llm_sim/infrastructure/patterns/llm_engine.py`
  - Copy `src/llm_sim/engines/llm_engine.py` → `src/llm_sim/infrastructure/patterns/llm_engine.py`
  - Update import: `from llm_sim.engines.base import BaseEngine` → `from llm_sim.infrastructure.base.engine import BaseEngine`
  - Keep original file for now

- [x] **T018 [P]** Move LLMValidator to `src/llm_sim/infrastructure/patterns/llm_validator.py`
  - Copy `src/llm_sim/validators/llm_validator.py` → `src/llm_sim/infrastructure/patterns/llm_validator.py`
  - Update import: `from llm_sim.validators.base import BaseValidator` → `from llm_sim.infrastructure.base.validator import BaseValidator`
  - Keep original file for now

### Move Concrete Implementations

- [x] **T019 [P]** Move EconLLMAgent to `src/llm_sim/implementations/agents/econ_llm_agent.py`
  - Copy `src/llm_sim/agents/econ_llm_agent.py` → `src/llm_sim/implementations/agents/econ_llm_agent.py`
  - Update import: `from llm_sim.agents.llm_agent import LLMAgent` → `from llm_sim.infrastructure.patterns.llm_agent import LLMAgent`
  - Keep original file for now

- [x] **T020 [P]** Move NationAgent to `src/llm_sim/implementations/agents/nation.py`
  - Copy `src/llm_sim/agents/nation.py` → `src/llm_sim/implementations/agents/nation.py`
  - Update import: `from llm_sim.agents.base import BaseAgent` → `from llm_sim.infrastructure.base.agent import BaseAgent`
  - Keep original file for now

- [x] **T021 [P]** Move EconLLMEngine to `src/llm_sim/implementations/engines/econ_llm_engine.py`
  - Copy `src/llm_sim/engines/econ_llm_engine.py` → `src/llm_sim/implementations/engines/econ_llm_engine.py`
  - Update import: `from llm_sim.engines.llm_engine import LLMEngine` → `from llm_sim.infrastructure.patterns.llm_engine import LLMEngine`
  - Keep original file for now

- [x] **T022 [P]** Move EconomicEngine to `src/llm_sim/implementations/engines/economic.py`
  - Copy `src/llm_sim/engines/economic.py` → `src/llm_sim/implementations/engines/economic.py`
  - Update imports to new infrastructure paths
  - Keep original file for now

- [x] **T023 [P]** Move EconLLMValidator to `src/llm_sim/implementations/validators/econ_llm_validator.py`
  - Copy `src/llm_sim/validators/econ_llm_validator.py` → `src/llm_sim/implementations/validators/econ_llm_validator.py`
  - Update import: `from llm_sim.validators.llm_validator import LLMValidator` → `from llm_sim.infrastructure.patterns.llm_validator import LLMValidator`
  - Keep original file for now

- [x] **T024 [P]** Move AlwaysValidValidator to `src/llm_sim/implementations/validators/always_valid.py`
  - Copy `src/llm_sim/validators/always_valid.py` → `src/llm_sim/implementations/validators/always_valid.py`
  - Update import: `from llm_sim.validators.base import BaseValidator` → `from llm_sim.infrastructure.base.validator import BaseValidator`
  - Keep original file for now

### Update __init__.py Files

- [x] **T025 [P]** Create convenience imports in `src/llm_sim/infrastructure/__init__.py`
  - Re-export BaseAgent, BaseEngine, BaseValidator
  - Re-export LLMAgent, LLMEngine, LLMValidator
  - Allow: `from llm_sim.infrastructure import BaseAgent`

- [x] **T026 [P]** Update `src/llm_sim/implementations/agents/__init__.py`
  - Empty for now (discovery handles imports)

- [x] **T027 [P]** Update `src/llm_sim/implementations/engines/__init__.py`
  - Empty for now (discovery handles imports)

- [x] **T028 [P]** Update `src/llm_sim/implementations/validators/__init__.py`
  - Empty for now (discovery handles imports)

## Phase 3.4: Discovery Mechanism Implementation

- [x] **T029** Implement ComponentDiscovery class in `src/llm_sim/discovery.py`
  - Implement `__init__(self, implementations_root: Path)`
  - Implement `_filename_to_classname(filename: str) -> str`
  - Implement `_load_module(component_type: str, filename: str) -> ModuleType`
  - Implement `_validate_inheritance(cls: Type, base_class: Type) -> None`
  - Implement `load_agent(filename: str) -> Type[BaseAgent]` with caching
  - Implement `load_engine(filename: str) -> Type[BaseEngine]` with caching
  - Implement `load_validator(filename: str) -> Type[BaseValidator]` with caching
  - Implement `list_agents() -> List[str]`
  - Implement `list_engines() -> List[str]`
  - Implement `list_validators() -> List[str]`
  - Add proper error messages per contract

- [x] **T030** Update orchestrator to use ComponentDiscovery in `src/llm_sim/orchestrator.py`
  - Import ComponentDiscovery
  - In `from_yaml`, instantiate `discovery = ComponentDiscovery(Path(__file__).parent)`
  - Replace agent loading: `discovery.load_agent(agent_config["type"])`
  - Replace engine loading: `discovery.load_engine(config["engine"]["type"])`
  - Replace validator loading: `discovery.load_validator(config["validator"]["type"])`
  - Remove old direct imports

## Phase 3.5: Test Updates (Update existing tests to new paths)

- [x] **T031** Update agent test imports in `tests/unit/test_base_interfaces.py`
  - Update BaseAgent import to new path
  - Run test to verify still passes

- [x] **T032** Update engine test imports in `tests/unit/test_economic_engine.py`
  - Update BaseEngine import to new path
  - Run test to verify still passes

- [x] **T033** Update validator test imports in `tests/unit/test_always_valid_validator.py`
  - Update BaseValidator import to new path
  - Run test to verify still passes

- [x] **T034** Update nation agent test imports in `tests/unit/test_nation_agent.py`
  - Update NationAgent import to new path
  - Run test to verify still passes

- [x] **T035** Update integration test imports in `tests/integration/test_simulation.py`
  - Update all agent/engine/validator imports to new paths
  - Run test to verify still passes

- [x] **T036** Update all contract test imports
  - Update imports in all tests/contract/ files
  - Ensure tests reference new infrastructure paths
  - Run contract tests to verify interfaces unchanged

## Phase 3.6: Cleanup & Finalization

- [x] **T037** Delete old agent files after verification
  - Delete `src/llm_sim/agents/base.py`
  - Delete `src/llm_sim/agents/llm_agent.py`
  - Delete `src/llm_sim/agents/econ_llm_agent.py`
  - Delete `src/llm_sim/agents/nation.py`
  - Keep `src/llm_sim/agents/__init__.py` but make it empty/deprecated marker

- [x] **T038** Delete old engine files after verification
  - Delete `src/llm_sim/engines/base.py`
  - Delete `src/llm_sim/engines/llm_engine.py`
  - Delete `src/llm_sim/engines/econ_llm_engine.py`
  - Delete `src/llm_sim/engines/economic.py`
  - Keep `src/llm_sim/engines/__init__.py` but make it empty/deprecated marker

- [x] **T039** Delete old validator files after verification
  - Delete `src/llm_sim/validators/base.py`
  - Delete `src/llm_sim/validators/llm_validator.py`
  - Delete `src/llm_sim/validators/econ_llm_validator.py`
  - Delete `src/llm_sim/validators/always_valid.py`
  - Keep `src/llm_sim/validators/__init__.py` but make it empty/deprecated marker

## Phase 3.7: Documentation

- [x] **T040 [P]** Create base classes documentation in `docs/patterns/base_classes.md`
  - Document BaseAgent interface and usage
  - Document BaseEngine interface and usage
  - Document BaseValidator interface and usage
  - Include examples of extending each

- [x] **T041 [P]** Create LLM pattern documentation in `docs/patterns/llm_pattern.md`
  - Document LLMAgent pattern and usage
  - Document LLMEngine pattern and usage
  - Document LLMValidator pattern and usage
  - Include examples and best practices

- [x] **T042 [P]** Create implementation guide in `docs/patterns/creating_implementations.md`
  - Explain directory structure
  - Explain naming conventions (snake_case → PascalCase)
  - Explain discovery mechanism
  - Include quickstart example
  - Document common pitfalls

- [x] **T043 [P]** Create migration guide in `docs/MIGRATION.md`
  - Document old → new import paths
  - Provide migration steps for users
  - Include example diff showing changes
  - Note backward compatibility via YAML configs

## Phase 3.8: Final Validation

- [x] **T044** Run full test suite with pytest
  - Run: `pytest tests/ -v`
  - Ensure all tests pass
  - Verify no import errors

- [x] **T045** Test backward compatibility with existing YAML config
  - Run simulation with existing config file
  - Verify output matches pre-reorganization behavior
  - Test with all sample configs

- [x] **T046** Verify discovery mechanism with manual test
  - Manually call `discovery.list_agents()` and verify all found
  - Manually load each implementation type
  - Verify error messages for invalid cases

- [x] **T047** Run linting and type checking
  - Run: `ruff check src/`
  - Run: `mypy src/`
  - Fix any issues found

- [x] **T048** Performance validation
  - Benchmark simulation runtime before/after
  - Ensure no degradation (< 5% overhead acceptable)
  - Profile discovery mechanism if needed

## Dependencies

**Setup before everything**:
- T001, T002, T003 must complete first

**Tests before implementation (TDD)**:
- T004-T012 (all tests) must complete before T013-T048 (implementation)

**Migration order**:
- T013-T015 (base classes) before T016-T018 (patterns) before T019-T024 (concrete)
- T025-T028 (__init__ files) after corresponding moves

**Discovery implementation**:
- T029 (discovery) requires T001-T002 (directories exist)
- T030 (orchestrator) requires T029 (discovery exists)

**Test updates**:
- T031-T036 require T013-T024 (files moved)

**Cleanup**:
- T037-T039 require T044-T046 (validation passed)

**Documentation anytime after setup**:
- T040-T043 can start after T003, run in parallel [P]

## Parallel Execution Examples

### Phase 3.2: All tests in parallel
```bash
# Launch T004-T012 together (9 test files, all [P]):
pytest tests/contract/test_base_agent_contract.py &
pytest tests/contract/test_base_engine_contract.py &
pytest tests/contract/test_base_validator_contract.py &
pytest tests/contract/test_llm_agent_contract.py &
pytest tests/contract/test_llm_engine_contract.py &
pytest tests/contract/test_llm_validator_contract.py &
pytest tests/unit/test_component_discovery.py &
pytest tests/integration/test_reorganized_simulation.py &
pytest tests/integration/test_backward_compatibility.py &
wait
```

### Phase 3.3: Move files in parallel (different components)
```bash
# Launch T013-T015 (base classes) together:
# Task: "Move BaseAgent to infrastructure/base/agent.py" &
# Task: "Move BaseEngine to infrastructure/base/engine.py" &
# Task: "Move BaseValidator to infrastructure/base/validator.py" &

# Then T016-T018 (patterns) together:
# Task: "Move LLMAgent to infrastructure/patterns/llm_agent.py" &
# Task: "Move LLMEngine to infrastructure/patterns/llm_engine.py" &
# Task: "Move LLMValidator to infrastructure/patterns/llm_validator.py" &

# Then T019-T024 (concrete implementations) together:
# Task: "Move EconLLMAgent..." &
# Task: "Move NationAgent..." &
# Task: "Move EconLLMEngine..." &
# Task: "Move EconomicEngine..." &
# Task: "Move EconLLMValidator..." &
# Task: "Move AlwaysValidValidator..." &
```

### Phase 3.7: Documentation in parallel
```bash
# Launch T040-T043 together (4 doc files, all [P]):
# Task: "Create base classes documentation in docs/patterns/base_classes.md" &
# Task: "Create LLM pattern documentation in docs/patterns/llm_pattern.md" &
# Task: "Create implementation guide in docs/patterns/creating_implementations.md" &
# Task: "Create migration guide in docs/MIGRATION.md" &
```

## Task Execution Notes

- **[P] tasks**: Different files, no dependencies - can run simultaneously
- **Sequential tasks**: Same file or dependencies - must run in order
- **Commit frequency**: Commit after each phase completion
- **Test verification**: After each move, run affected tests immediately
- **Rollback strategy**: Keep old files until T044-T046 validation passes

## Validation Checklist
*GATE: All must pass before marking complete*

- [ ] All contract tests (T004-T009) exist and initially fail
- [ ] All moved files have updated imports (T013-T024)
- [ ] ComponentDiscovery implements all methods (T029)
- [ ] Orchestrator uses discovery mechanism (T030)
- [ ] All existing tests updated and passing (T031-T036, T044)
- [ ] Old files deleted (T037-T039)
- [ ] All documentation created (T040-T043)
- [ ] Backward compatibility verified (T045)
- [ ] Performance acceptable (T048)
- [ ] No task modifies same file as another [P] task

## Total: 48 Tasks
- Setup: 3 tasks (T001-T003)
- Tests (TDD): 9 tasks (T004-T012) - all [P]
- Migration: 13 tasks (T013-T024) - mostly [P] by component
- __init__ updates: 4 tasks (T025-T028) - all [P]
- Discovery: 2 tasks (T029-T030) - sequential
- Test updates: 6 tasks (T031-T036) - can be [P] within groups
- Cleanup: 3 tasks (T037-T039) - [P] by component
- Documentation: 4 tasks (T040-T043) - all [P]
- Validation: 5 tasks (T044-T048) - sequential

**Estimated parallel execution time**: 40-50% reduction vs sequential (due to 25+ [P] tasks)
