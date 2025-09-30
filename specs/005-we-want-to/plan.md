# Implementation Plan: Separate Simulation Infrastructure from Domain Implementations

**Branch**: `005-we-want-to` | **Date**: 2025-09-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/hendrik/coding/llm_sim/llm_sim/specs/005-we-want-to/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
2. Fill Technical Context ✓
3. Fill Constitution Check section ✓
4. Evaluate Constitution Check → No violations
5. Execute Phase 0 → research.md ✓
6. Execute Phase 1 → contracts, data-model.md, quickstart.md ✓
7. Re-evaluate Constitution Check → PASS
8. Plan Phase 2 → Task generation approach described
9. STOP - Ready for /tasks command
```

## Summary
Reorganize the simulation framework to separate abstract infrastructure (BaseAgent, BaseEngine, BaseValidator, LLMAgent, LLMEngine, LLMValidator) from concrete domain implementations (EconLLMAgent, NationAgent, etc.). The reorganization will use directory-based discovery where configuration files reference concrete implementations by filename only, maintaining backward compatibility while enabling easy creation of new simulation domains.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama, httpx
**Storage**: File system (YAML configs, Python modules)
**Testing**: pytest with async support, pytest-mock
**Target Platform**: Linux server (Python runtime)
**Project Type**: Single project (library + CLI)
**Performance Goals**: Maintain current simulation performance (no degradation from reorganization)
**Constraints**:
- Backward compatibility with existing YAML configs
- No breaking changes to orchestrator API
- Directory-based discovery must be reliable
**Scale/Scope**:
- ~15 Python modules to reorganize
- 2 abstract base classes (Base*), 3 LLM pattern classes (LLM*), 4+ concrete implementations
- Maintain all existing tests

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is not yet defined (template form). For this refactoring feature:

**Design Principles Applied**:
- ✅ Clear separation of concerns (abstract vs concrete)
- ✅ File-based discovery for simplicity
- ✅ Backward compatibility maintained
- ✅ Test coverage preserved and extended

**No violations detected** - This is a refactoring/reorganization task that improves architecture clarity without adding complexity.

## Project Structure

### Documentation (this feature)
```
specs/005-we-want-to/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/tasks command)
```

### Source Code (repository root)
```
src/llm_sim/
├── infrastructure/      # NEW: Abstract infrastructure
│   ├── base/           # Base abstract classes
│   │   ├── agent.py    # BaseAgent
│   │   ├── engine.py   # BaseEngine
│   │   └── validator.py # BaseValidator
│   └── patterns/       # Pattern-providing abstract classes
│       ├── llm_agent.py    # LLMAgent
│       ├── llm_engine.py   # LLMEngine
│       └── llm_validator.py # LLMValidator
│
├── implementations/     # NEW: Concrete domain implementations
│   ├── agents/
│   │   ├── econ_llm_agent.py
│   │   └── nation.py
│   ├── engines/
│   │   ├── econ_llm_engine.py
│   │   └── economic.py
│   └── validators/
│       ├── econ_llm_validator.py
│       ├── always_valid.py
│       └── llm_validator_base.py (if needed)
│
├── models/             # Unchanged
├── utils/              # Unchanged
├── orchestrator.py     # Updated: discovery logic
└── __init__.py

tests/
├── contract/           # Updated paths
├── integration/        # Updated paths
└── unit/              # Updated paths

docs/                   # NEW: Pattern documentation
└── patterns/
    ├── base_classes.md
    ├── llm_pattern.md
    └── creating_implementations.md
```

**Structure Decision**: Single project structure with new `infrastructure/` and `implementations/` top-level directories under `src/llm_sim/`. Abstract classes separated by level (base vs patterns), concrete implementations organized by component type (agents, engines, validators).

## Phase 0: Outline & Research

**Unknowns to research**:
1. ✅ Python module discovery patterns (importlib, __init__.py strategies)
2. ✅ Directory scanning for dynamic class loading
3. ✅ Backward compatibility strategies for import paths
4. ✅ Testing patterns for reorganized codebases

**Research findings** documented in [research.md](./research.md)

## Phase 1: Design & Contracts

**Entities** (documented in [data-model.md](./data-model.md)):
- Directory structures for infrastructure vs implementations
- Module import paths (old → new mapping)
- Discovery mechanism interface
- Configuration schema (filename-based references)

**Contracts** (in `/contracts/`):
- Orchestrator discovery API contract
- Abstract class interface contracts (BaseAgent, BaseEngine, BaseValidator)
- LLM pattern contracts (LLMAgent, LLMEngine, LLMValidator)
- Concrete implementation examples

**Tests**:
- Contract tests for all abstract interfaces
- Discovery mechanism tests
- Import compatibility tests
- Integration tests with reorganized structure

**Output**: data-model.md, contracts/, quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Migration tasks** (preserve existing functionality):
   - Create new directory structure
   - Move abstract base classes to `infrastructure/base/`
   - Move LLM pattern classes to `infrastructure/patterns/`
   - Move concrete implementations to `implementations/`
   - Update all import paths in moved files

2. **Discovery mechanism tasks**:
   - Implement filename-based discovery in orchestrator
   - Add validation for concrete implementations
   - Update configuration loading

3. **Documentation tasks**:
   - Create pattern documentation files
   - Update existing docs with new structure
   - Create migration guide for users

4. **Testing tasks** (TDD order):
   - Write contract tests for abstract interfaces
   - Write discovery mechanism tests
   - Write import compatibility tests
   - Update existing tests with new paths
   - Run full test suite validation

**Ordering Strategy**:
- Phase A: Create new directories and documentation structure
- Phase B: Move files with import path updates (can be parallelized by component type)
- Phase C: Implement discovery mechanism with tests
- Phase D: Update orchestrator and configuration loading
- Phase E: Comprehensive testing and validation

**Estimated Output**: 35-40 tasks covering migration, discovery, testing, and documentation

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md with file moves, import updates, discovery mechanism)
**Phase 5**: Validation (all tests pass, backward compatibility verified, documentation complete)

## Complexity Tracking
*No constitutional violations - section intentionally empty*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on project requirements - See `/specs/005-we-want-to/spec.md`*
