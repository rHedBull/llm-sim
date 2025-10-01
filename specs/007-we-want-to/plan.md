# Implementation Plan: Abstract Agent and Global State System

**Branch**: `007-we-want-to` | **Date**: 2025-10-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-we-want-to/spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
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
Enable simulation configurations to define custom state variables for agents and global state through YAML configuration, replacing hardcoded variables like `economic_strength` and `inflation` with a flexible type system supporting float, int, boolean, and categorical types with validation and constraint enforcement.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (data modeling), PyYAML 6.x (config parsing), structlog 24.x (logging)
**Storage**: File system (JSON checkpoint files in `output/` directory)
**Testing**: pytest (existing test suite in `tests/`)
**Target Platform**: Linux/macOS development environments
**Project Type**: single (Python package with CLI)
**Performance Goals**: Config validation at startup (<100ms), constraint enforcement per variable update (<1ms)
**Constraints**: Strict checkpoint schema compatibility (reject incompatible loads), fail-fast config validation
**Scale/Scope**: Support 10-50 custom variables per simulation, 2-100 agents per simulation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: Constitution file is template placeholder - no specific project constraints defined.

No constitutional violations detected. Proceeding with standard design approach.

## Project Structure

### Documentation (this feature)
```
specs/007-we-want-to/
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
│   ├── state.py              # MODIFY: Abstract AgentState, GlobalState
│   ├── config.py             # MODIFY: Add variable definition models
│   ├── checkpoint.py         # EXISTS: Checkpoint models
│   └── __init__.py
├── infrastructure/
│   ├── base/                 # EXISTS: Base classes
│   └── patterns/             # EXISTS: Pattern implementations
├── implementations/
│   ├── agents/               # EXISTS: Agent implementations
│   ├── engines/              # EXISTS: Engine implementations
│   └── validators/           # EXISTS: Validator implementations
├── persistence/
│   ├── checkpoint_manager.py # MODIFY: Schema validation on load
│   ├── storage.py            # EXISTS: Storage operations
│   └── __init__.py
├── validators/               # EXISTS: Validation utilities
│   └── __init__.py
├── utils/
│   └── __init__.py
└── orchestrator.py           # MODIFY: Use abstract state models

tests/
├── unit/                     # ADD: Unit tests for variable system
├── integration/              # ADD: Integration tests for end-to-end flows
└── contract/                 # ADD: Contract tests for config schemas

examples/
├── basic_economic.yaml       # MODIFY: Update with variable definitions
├── llm_economic.yaml         # MODIFY: Update with variable definitions
└── military_simulation.yaml  # ADD: New example showing different variables
```

**Structure Decision**: Single Python package with src/llm_sim as root module. Existing structure uses infrastructure/base for abstractions and implementations/ for concrete types. This feature extends the models/ and config system to support dynamic variable definitions.

## Phase 0: Outline & Research
*Status: Complete*

### Research Questions Addressed

#### 1. Pydantic Dynamic Model Creation
**Decision**: Use Pydantic's `create_model()` for runtime model generation
**Rationale**:
- Allows dynamic field creation from YAML config
- Preserves type safety and validation
- Maintains serialization compatibility with existing checkpoint system
**Alternatives considered**:
- Dict-based state (rejected: loses type safety, validation)
- Metaclasses (rejected: overly complex, harder to debug)

#### 2. Type System Design
**Decision**: Four core types: `float`, `int`, `bool`, `categorical`
**Rationale**:
- Covers use cases from spec (economic metrics, flags, enums)
- Maps cleanly to Pydantic field types
- Simple validation rules
**Alternatives considered**:
- String type (deferred: not in initial requirements)
- Complex types like lists/dicts (deferred: not in initial requirements)

#### 3. Constraint Enforcement Strategy
**Decision**: Validation in Pydantic field validators + custom setter logic
**Rationale**:
- Pydantic validators handle type checking automatically
- Field(ge=, le=) for numeric min/max
- Literal[] for categorical validation
- Centralized validation logic
**Alternatives considered**:
- Manual checks in engine (rejected: scattered logic, error-prone)
- Property decorators (rejected: doesn't work with frozen models)

#### 4. Checkpoint Schema Compatibility
**Decision**: Store variable schema in checkpoint metadata, validate on load
**Rationale**:
- Per FR-007a: strict compatibility required
- Schema hash or full schema comparison
- Clear error messages on mismatch
**Alternatives considered**:
- Schema migration (rejected: explicit requirement to reject)
- Best-effort merge (rejected: explicit requirement to reject)

#### 5. Config YAML Structure
**Decision**: Nested structure under `state_variables` key
```yaml
state_variables:
  agent_vars:
    gdp:
      type: float
      min: 0
      max: 1000000
      default: 1000.0
    population:
      type: int
      min: 1
      default: 1000000
  global_vars:
    inflation:
      type: float
      min: -1.0
      max: 1.0
      default: 0.02
    open_economy:
      type: bool
      default: true
    tech_era:
      type: categorical
      values: [stone, bronze, iron, steel]
      default: bronze
```
**Rationale**:
- Clear separation of agent vs global variables
- Self-documenting structure
- Extensible for future additions
**Alternatives considered**:
- Flat structure (rejected: unclear ownership)
- Separate files (rejected: unnecessary complexity)

## Phase 1: Design & Contracts
*Status: Complete*

### Design Artifacts Generated
1. **data-model.md**: Entity definitions for VariableDefinition, AgentState, GlobalState, SimulationState
2. **contracts/config-schema.json**: JSON Schema for YAML config validation
3. **contracts/checkpoint-schema.json**: JSON Schema for checkpoint format with schema metadata
4. **quickstart.md**: Step-by-step guide to create a custom simulation
5. **CLAUDE.md**: Updated with new technologies and structure

### Key Design Decisions

#### Variable Definition Model
```python
# Conceptual structure (details in data-model.md)
class VariableDefinition:
    name: str
    var_type: Literal["float", "int", "bool", "categorical"]
    min_value: Optional[float]  # For float/int
    max_value: Optional[float]  # For float/int
    allowed_values: Optional[List[str]]  # For categorical
    default: Union[float, int, bool, str]
```

#### Dynamic State Model Creation
- Factory functions `create_agent_state_model()` and `create_global_state_model()`
- Generate Pydantic models at config load time
- Register with checkpoint system for schema tracking

#### Backward Compatibility
- Existing configs without `state_variables` section use implicit defaults
- Default agent vars: `{economic_strength: {type: float, min: 0, default: 0}}`
- Default global vars: `{interest_rate: {type: float}, total_economic_value: {type: float}, gdp_growth: {type: float}, inflation: {type: float}, unemployment: {type: float}}`
- Deprecation warning logged for configs without explicit variable definitions

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate from Phase 1 artifacts:
   - Contract tests for config schema validation
   - Contract tests for checkpoint schema validation
   - Unit tests for VariableDefinition validation logic
   - Unit tests for dynamic model creation
   - Unit tests for constraint enforcement
   - Integration tests for each acceptance scenario from spec
   - Implementation tasks for each contract/test
3. Follow TDD order: tests before implementation
4. Mark parallel-safe tasks with [P]

**Ordering Strategy**:
1. **Config Layer** (P): Variable definition models, validation
2. **State Layer** (P): Dynamic AgentState/GlobalState creation
3. **Persistence Layer**: Checkpoint schema metadata, validation on load
4. **Integration**: Orchestrator updates, end-to-end tests
5. **Examples**: Update existing configs, add new examples
6. **Migration**: Deprecation warnings, backward compatibility

**Estimated Output**: 30-35 numbered, dependency-ordered tasks

**Task Categories**:
- Contract Tests: 4 tasks
- Unit Tests: 12 tasks
- Integration Tests: 7 tasks (one per acceptance scenario)
- Implementation: 15 tasks
- Documentation/Examples: 3 tasks

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD principles)
**Phase 5**: Validation (run tests, execute quickstart.md, verify examples)

## Complexity Tracking
*No constitutional violations requiring justification*

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
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (N/A)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
