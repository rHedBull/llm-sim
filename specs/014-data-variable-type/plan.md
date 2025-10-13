# Implementation Plan: Complex Data Type Support for State Variables

**Branch**: `014-data-variable-type` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-data-variable-type/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend the VariableDefinition system to support complex data types (dict, list, tuple, str, object) beyond the current scalar types (float, int, bool, categorical). This enables modeling of real-world simulations with inventories, coordinates, histories, and nested structures while maintaining type safety through Pydantic validation.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (validation), PyYAML 6.x (config), structlog 24.x (logging), NetworkX 3.5 (existing spatial infrastructure)
**Storage**: File system (JSON checkpoints in `output/` directory)
**Testing**: pytest 8.0+ with coverage (target 90% for core, 80% for implementations)
**Target Platform**: Linux/macOS/Windows - CLI-based simulation framework
**Project Type**: Single project (src/ + tests/ structure)
**Performance Goals**: Validation <10ms for typical state (100 agents × 50 variables with 3 dicts, 2 lists, 1 tuple each)
**Constraints**:
  - Max nesting depth: 4 levels for dict, 3 levels for list
  - Max collection size: 1000 items per dict or list
  - Must maintain backward compatibility with existing scalar-only configs
  - No performance regression for scalar-only simulations (<5% difference)
**Scale/Scope**: Support simulations with 100-1000 agents, each having complex state with nested collections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle 1 - Simplicity First**: ✅ PASS
- Extending existing VariableDefinition pattern rather than introducing new abstraction layer
- Reusing Pydantic's built-in validation rather than custom validation logic
- Simple type hierarchy: scalar types → complex types (dict, list, tuple, str, object)

**Principle 2 - Single Source of Truth**: ✅ PASS
- VariableDefinition remains single location for type schema definition
- create_agent_state_model() and create_global_state_model() factories generate models from definitions
- No duplication of validation logic - all handled by extended VariableDefinition

**Principle 3 - No Legacy Support**: ✅ PASS
- Backward compatible with existing scalar-only configs through type system extension
- No silent fallbacks - new types require explicit declaration
- Old configs work unchanged; new types require explicit opt-in

**Principle 4 - Test-First Development**: ✅ WILL ENFORCE
- Tasks.md (Phase 2) will mandate test-first approach
- Each user story has independent test scenarios
- Red-Green-Refactor cycle required for all implementations

**Principle 5 - Clean Interface Design**: ✅ PASS
- VariableDefinition extension maintains explicit type annotations
- Factory functions have clear single responsibility
- Validation errors include full field paths (e.g., "agent_state.inventory.food")

**Principle 6 - Observability**: ✅ PASS
- Structured logging via structlog for validation operations
- Error messages include: field path, expected type, actual value, remediation steps
- Performance metrics logged for validation timing

**Principle 7 - uv Package Management**: ✅ PASS
- All dependencies already in pyproject.toml managed by uv
- No new dependencies required (using existing Pydantic 2.x features)
- Tests will run via `uv run pytest`

**Result**: ALL GATES PASS - Proceed to Phase 0

---

## Post-Design Constitution Re-Check

*Re-evaluation after Phase 1 design completion*

**Principle 1 - Simplicity First**: ✅ PASS (CONFIRMED)
- Design uses native Pydantic 2.x features without custom abstractions
- Two-mode dict approach (dynamic keys vs fixed schema) maps to natural Pydantic patterns
- No new complexity layers introduced beyond extending VariableDefinition

**Principle 2 - Single Source of Truth**: ✅ PASS (CONFIRMED)
- VariableDefinition remains sole source of schema truth
- JSON Schema contract (contracts/variable_definition.json) is generated documentation, not a second source
- All validation rules defined once in VariableDefinition, enforced by Pydantic

**Principle 3 - No Legacy Support**: ✅ PASS (CONFIRMED)
- Design maintains backward compatibility without silent fallbacks
- New types require explicit declaration in config
- Old scalar-only configs work unchanged (extension, not modification)

**Principle 4 - Test-First Development**: ✅ WILL ENFORCE (PENDING)
- data-model.md specifies validation rules that will be test cases
- tasks.md (Phase 2) will mandate TDD approach
- Each user story from spec.md has independent test scenarios

**Principle 5 - Clean Interface Design**: ✅ PASS (CONFIRMED)
- VariableDefinition extension maintains explicit type annotations
- Type-specific fields clearly documented (key_type vs value_type vs schema)
- Error messages include full dot-notation paths (agent_state.inventory.food)

**Principle 6 - Observability**: ✅ PASS (CONFIRMED)
- Error format specified in data-model.md with field paths and context
- Performance monitoring planned (tracemalloc, benchmarking)
- Validation timing will be logged for analysis

**Principle 7 - uv Package Management**: ✅ PASS (CONFIRMED)
- No new dependencies required beyond existing Pydantic 2.x
- All tests will run via `uv run pytest`
- Agent context updated in CLAUDE.md

**Final Result**: ALL GATES PASS POST-DESIGN - Proceed to Phase 2 (tasks.md generation)

## Project Structure

### Documentation (this feature)

```
specs/014-data-variable-type/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── variable_definition.json  # Extended VariableDefinition schema
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/llm_sim/
├── models/
│   ├── config.py        # [MODIFY] VariableDefinition extension for complex types
│   ├── state.py         # [MODIFY] Factory functions to handle complex types
│   └── exceptions.py    # [NEW] Complex type validation exceptions
├── validators/
│   └── complex_types.py # [NEW] Validation logic for nested structures
├── persistence/
│   └── checkpoint_manager.py  # [MODIFY] Handle serialization of complex types
└── utils/
    └── type_helpers.py  # [NEW] Helper functions for type inspection/validation

tests/
├── unit/
│   ├── test_variable_definition.py  # [MODIFY] Tests for extended VariableDefinition
│   ├── test_state_models.py         # [MODIFY] Tests for complex type state models
│   ├── test_complex_validators.py   # [NEW] Tests for complex type validation
│   └── test_serialization.py        # [NEW] Tests for checkpoint round-trip with complex types
├── integration/
│   ├── test_complex_simulation.py   # [NEW] End-to-end test with complex types
│   └── test_backward_compat.py      # [NEW] Ensure scalar-only configs still work
└── performance/
    └── test_validation_perf.py      # [NEW] Validation performance benchmarks

examples/
└── trading_simulation.yaml          # [NEW] Example config demonstrating all complex types
```

**Structure Decision**: Single project structure (Option 1) is appropriate. This is a core framework extension that modifies existing models and adds validation infrastructure. All changes are within the existing `src/llm_sim/` namespace with corresponding test coverage. No new top-level directories or services required.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**NO VIOLATIONS** - All constitution principles pass without justified exceptions.
