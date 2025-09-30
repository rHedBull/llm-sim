# Research: Separating Simulation Infrastructure from Domain Implementations

**Feature**: 005-we-want-to | **Date**: 2025-09-30

## Research Questions

### 1. Python Module Discovery Patterns

**Decision**: Use `importlib` with explicit directory scanning for concrete implementations

**Rationale**:
- `importlib.import_module()` provides reliable dynamic imports
- Directory scanning with `pathlib` is straightforward and maintainable
- Avoids complex metaclass or plugin registration systems
- Works well with Python 3.12's module system

**Alternatives Considered**:
- **Entry points (setuptools)**: Too heavyweight for internal reorganization, requires package installation
- **Metaclass registration**: Automatic but adds complexity and "magic" behavior
- **__init__.py imports**: Simple but requires updating __init__.py for every new implementation (defeats purpose)

**Implementation approach**:
```python
from pathlib import Path
import importlib.util

def discover_implementations(directory: Path, base_class):
    """Scan directory for Python files and load classes that inherit from base_class"""
    for py_file in directory.glob("*.py"):
        if py_file.stem.startswith("_"):
            continue
        # Load module and inspect for classes
```

### 2. Directory Scanning for Dynamic Class Loading

**Decision**: Convention-based scanning with class name matching

**Rationale**:
- Filename `econ_llm_agent.py` → expect class `EconLLMAgent`
- Simple convention: CamelCase class name from snake_case filename
- Validation at load time ensures correct implementation
- Clear error messages when conventions not followed

**Alternatives Considered**:
- **Explicit registration**: Requires decorators or manual registration calls (more boilerplate)
- **Config-based mapping**: YAML files mapping names to classes (extra configuration burden)
- **Auto-discovery all classes**: Could pick up test classes or helpers accidentally

**Implementation approach**:
```python
def filename_to_classname(filename: str) -> str:
    """Convert econ_llm_agent.py → EconLLMAgent"""
    return ''.join(word.capitalize() for word in filename.split('_'))

def load_implementation(filename: str, base_class):
    """Load and validate implementation"""
    expected_class = filename_to_classname(Path(filename).stem)
    module = import_module(f"llm_sim.implementations.{component_type}.{filename}")
    cls = getattr(module, expected_class)
    if not issubclass(cls, base_class):
        raise TypeError(f"{cls} must inherit from {base_class}")
    return cls
```

### 3. Backward Compatibility Strategies for Import Paths

**Decision**: No import path compatibility layer needed - YAML configs use filenames only

**Rationale**:
- Current design: YAML configs reference implementations by filename (e.g., `agent: econ_llm_agent`)
- Filenames stay the same, only directory structure changes
- Orchestrator handles discovery, user code doesn't import directly
- Tests will need import path updates (acceptable for internal code)

**Alternatives Considered**:
- **Compatibility shims**: Create old paths that re-export from new locations
  - Con: Maintains technical debt, delays migration
  - Pro: Zero code changes needed
  - **Rejected**: Clean break better for long-term maintenance

- **Gradual migration**: Support both old and new imports
  - Con: Complex to maintain dual system
  - Pro: Gentler transition period
  - **Rejected**: Small codebase, can update in one pass

**Migration strategy**:
1. Update all test imports in one commit
2. Update any direct imports in orchestrator/utils
3. Verify YAML configs still work (filenames unchanged)
4. Document new import paths for developers

### 4. Testing Patterns for Reorganized Codebases

**Decision**: Multi-layered testing with contract tests as foundation

**Rationale**:
- **Contract tests**: Verify abstract interfaces haven't changed
- **Discovery tests**: Ensure file scanning and class loading works
- **Integration tests**: Validate orchestrator with reorganized structure
- **Regression tests**: Existing tests updated to new imports

**Test organization**:
```
tests/
├── contract/
│   ├── test_base_agent_contract.py        # BaseAgent interface stability
│   ├── test_llm_agent_contract.py         # LLMAgent interface stability
│   └── test_discovery_contract.py         # Discovery API contract
├── integration/
│   ├── test_reorganized_simulation.py     # End-to-end with new structure
│   └── test_backward_compatibility.py     # YAML configs still work
└── unit/
    ├── test_discovery_mechanism.py        # File scanning logic
    └── test_class_loading.py              # Dynamic import logic
```

**Alternatives Considered**:
- **Snapshot testing**: Compare before/after behavior
  - Pro: Catches unexpected changes
  - Con: Can be brittle, hard to understand failures
  - **Partial adoption**: Use for orchestrator output only

- **Property-based testing**: Generate random valid configs
  - Pro: Broad coverage
  - Con: Overkill for file reorganization
  - **Rejected**: Standard test cases sufficient

### 5. Directory Structure Best Practices

**Decision**: Separate `infrastructure/` and `implementations/` at top level

**Rationale**:
- **Clear conceptual separation**: infrastructure = abstract, implementations = concrete
- **Easy to navigate**: Developers know where to add new domain implementations
- **Scalable**: Can add more pattern subdirectories under infrastructure/
- **Documentation-friendly**: Each section can have its own README

**Structure**:
```
src/llm_sim/
├── infrastructure/     # Never change unless adding new patterns
│   ├── base/          # Minimal abstract interfaces
│   └── patterns/      # Reusable abstract implementations
├── implementations/    # Add new domains here
│   ├── agents/
│   ├── engines/
│   └── validators/
```

**Alternatives Considered**:
- **Flat structure** with `abstract_` and `concrete_` prefixes
  - Con: Still mixed in same directory
  - Con: Doesn't scale well

- **Component-first** (agents/, engines/, validators/ with abstract/concrete subdirs)
  - Con: Abstract classes spread across multiple directories
  - Con: Harder to see full infrastructure at a glance

## Key Findings Summary

1. **Discovery mechanism**: `importlib` + convention-based class name matching
2. **Backward compatibility**: Maintained via filename stability in YAML configs
3. **Testing strategy**: Contract tests + discovery tests + integration tests
4. **Directory organization**: `infrastructure/` vs `implementations/` split
5. **Migration approach**: One-time import path updates, comprehensive test coverage

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Discovery mechanism fails for edge cases | High | Comprehensive unit tests for file scanning |
| Import path updates break tests | Medium | Systematic find-replace + test all |
| Users confused by new structure | Low | Clear documentation + migration guide |
| Performance degradation from dynamic loading | Low | Benchmark before/after, cache loaded classes |

## Dependencies

No new external dependencies required. Uses standard library:
- `importlib` (Python 3.12 stdlib)
- `pathlib` (Python 3.12 stdlib)
- `inspect` (Python 3.12 stdlib)

## Next Steps

Proceed to Phase 1: Design & Contracts
- Define discovery mechanism API contract
- Document directory structure formally
- Create contract tests for abstract interfaces
- Design backward compatibility verification tests
