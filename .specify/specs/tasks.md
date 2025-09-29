# Implementation Tasks: Simulation Loop

## Pre-Implementation Checklist
- [x] Review all constitution principles
- [ ] Write tests first (TDD)
- [ ] Get test approval before implementation
- [x] Identify reusable components in existing codebase
- [x] Plan simplest possible implementation
- [x] Design explicit, type-annotated interfaces
- [x] Plan observability and error handling
- [x] Ensure clean transitions without compatibility layers

## Task Categories

### Setup Tasks
- [ ] Initialize project structure with uv
- [ ] Add core dependencies (pydantic, pyyaml, structlog)
- [ ] Set up testing framework (pytest)
- [ ] Configure code quality tools (black, ruff, mypy)

### Core Implementation Tasks

#### 1. **Project Setup**
   - Complexity: Low
   - Reuses: uv package manager
   - Creates: Project structure
   - Dependencies: None
   - Subtasks:
     - [ ] Update pyproject.toml with dependencies
     - [ ] Create src/llm_sim module structure
     - [ ] Set up logging configuration

#### 2. **Data Models**
   - Complexity: Low
   - Reuses: Pydantic BaseModel
   - Creates: State, Action, Config models
   - Dependencies: Project Setup
   - Subtasks:
     - [ ] Write tests for SimulationState model
     - [ ] Implement SimulationState with pydantic
     - [ ] Write tests for Action model
     - [ ] Implement Action with validation marking
     - [ ] Write tests for SimulationConfig
     - [ ] Implement SimulationConfig for YAML parsing

#### 3. **Base Interfaces**
   - Complexity: Low
   - Reuses: Python ABC
   - Creates: BaseEngine, BaseAgent, BaseValidator
   - Dependencies: Data Models
   - Subtasks:
     - [ ] Write tests for BaseEngine interface
     - [ ] Implement BaseEngine ABC
     - [ ] Write tests for BaseAgent interface
     - [ ] Implement BaseAgent ABC
     - [ ] Write tests for BaseValidator interface
     - [ ] Implement BaseValidator ABC

#### 4. **Economic Engine**
   - Complexity: Medium (justified: core business logic)
   - Reuses: BaseEngine interface
   - Creates: EconomicEngine implementation
   - Dependencies: Base Interfaces
   - Subtasks:
     - [ ] Write tests for state initialization
     - [ ] Implement initialize_state method
     - [ ] Write tests for interest application
     - [ ] Implement apply_engine_rules with interest
     - [ ] Write tests for termination conditions
     - [ ] Implement check_termination logic

#### 5. **Nation Agent**
   - Complexity: Low
   - Reuses: BaseAgent interface
   - Creates: NationAgent implementation
   - Dependencies: Base Interfaces
   - Subtasks:
     - [ ] Write tests for fixed action strategy
     - [ ] Implement NationAgent with fixed actions
     - [ ] Write tests for state reception
     - [ ] Implement receive_state method

#### 6. **Always Valid Validator**
   - Complexity: Low
   - Reuses: BaseValidator interface
   - Creates: AlwaysValidValidator implementation
   - Dependencies: Base Interfaces
   - Subtasks:
     - [ ] Write tests for validation (always true)
     - [ ] Implement AlwaysValidValidator
     - [ ] Write tests for action marking
     - [ ] Implement statistics tracking

#### 7. **Simulation Orchestrator**
   - Complexity: Medium (justified: coordinates components)
   - Reuses: All base classes
   - Creates: Main simulation loop
   - Dependencies: All components
   - Subtasks:
     - [ ] Write integration tests for simulation
     - [ ] Implement configuration loading
     - [ ] Implement component initialization
     - [ ] Implement turn-based loop
     - [ ] Implement result collection

#### 8. **CLI Interface**
   - Complexity: Low
   - Reuses: argparse, pathlib
   - Creates: Command-line entry point
   - Dependencies: Simulation Orchestrator
   - Subtasks:
     - [ ] Write tests for CLI arguments
     - [ ] Implement main.py entry point
     - [ ] Add debug mode support
     - [ ] Add output formatting options

#### 9. **Example Configurations**
   - Complexity: Low
   - Reuses: YAML format
   - Creates: Example config files
   - Dependencies: None
   - Subtasks:
     - [ ] Create basic economic simulation config
     - [ ] Create quick test config (5 turns)
     - [ ] Create extended test config (100 turns)

### Testing Tasks
- [ ] Unit tests for each component (90% coverage)
- [ ] Integration test for full simulation run
- [ ] Edge case tests (termination conditions)
- [ ] Performance test (1000 turns)

### Documentation Tasks
- [ ] Update README with usage instructions
- [ ] Add inline documentation for complex logic only
- [ ] Create examples directory with demos

## Task Prioritization

### Phase 1: Foundation (Tasks 1-3)
1. Project Setup
2. Data Models
3. Base Interfaces

### Phase 2: Core Components (Tasks 4-6)
4. Economic Engine
5. Nation Agent
6. Always Valid Validator

### Phase 3: Integration (Tasks 7-9)
7. Simulation Orchestrator
8. CLI Interface
9. Example Configurations

### Phase 4: Quality Assurance
- Complete test coverage
- Documentation updates
- Code quality checks

## Validation Steps
- [ ] Each component has single responsibility
- [ ] No code duplication across components
- [ ] All interfaces are type-annotated
- [ ] Error messages include context and remediation
- [ ] Tests written before implementation

## Post-Implementation Review
- [ ] Code follows KISS principle (simple and clear)
- [ ] No duplication (DRY compliance)
- [ ] Clean architecture without legacy support
- [ ] Tests pass and provide good coverage
- [ ] Interfaces are explicit and composable
- [ ] Logging provides good observability

## Execution Order

### Day 1: Foundation
1. Project Setup (30 min)
2. Data Models with tests (2 hours)
3. Base Interfaces with tests (2 hours)

### Day 2: Components
4. Economic Engine with tests (2 hours)
5. Nation Agent with tests (1 hour)
6. Always Valid Validator with tests (1 hour)

### Day 3: Integration
7. Simulation Orchestrator with tests (3 hours)
8. CLI Interface (1 hour)

### Day 4: Polish
9. Example Configurations (30 min)
10. Documentation (1 hour)
11. Code quality checks (30 min)
12. Final testing (1 hour)

## Success Metrics
- All tests passing
- 90%+ code coverage
- No mypy errors
- Clean ruff/black checks
- Simulation runs successfully
- Clear logging output
- Documentation complete