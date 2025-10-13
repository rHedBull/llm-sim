# llm_sim Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.12 + Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama Python client (new), httpx (for async LLM calls) (004-new-feature-i)
- Python 3.12 + Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama, httpx (005-we-want-to)
- File system (YAML configs, Python modules) (005-we-want-to)
- Python 3.12 + Pydantic 2.x (serialization), PyYAML 6.x (config), structlog 24.x (logging) (006-persistent-storage-specifically)
- File system (JSON files in `output/` directory) (006-persistent-storage-specifically)
- Python 3.12 + Pydantic 2.x (data modeling), PyYAML 6.x (config parsing), structlog 24.x (logging) (007-we-want-to)
- File system (JSON checkpoint files in `output/` directory) (007-we-want-to)
- Python 3.12 + Pydantic 2.x (data models), PyYAML 6.x (config), structlog 24.x (logging) (009-dynamic-agent-management)
- Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), httpx (async I/O), FastAPI (API server) (010-event-stream-the)
- File system (JSONL files in output/{run_id}/events*.jsonl) (010-event-stream-the)
- Python 3.12 + structlog 24.x (existing), Python stdlib contextvars (011-logging-improvements-enhanced)
- N/A (logging only - outputs to stdout/files) (011-logging-improvements-enhanced)
- Python 3.12 + Pydantic 2.x (state models), PyYAML 6.x (config), structlog 24.x (logging), NetworkX (graph algorithms for shortest path) (012-spatial-maps)
- File system (YAML configs, JSON checkpoints for spatial state persistence) (012-spatial-maps)
- Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), aiofiles (async I/O for async mode) (013-event-writer-fix)
- File system (JSONL files in `output/{run_id}/events.jsonl`) (013-event-writer-fix)
- Python 3.12 + Pydantic 2.x (validation), PyYAML 6.x (config), structlog 24.x (logging), NetworkX 3.5 (existing spatial infrastructure) (014-data-variable-type)
- File system (JSON checkpoints in `output/` directory) (014-data-variable-type)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.12: Follow standard conventions

## Recent Changes
- 014-data-variable-type: ✅ **COMPLETED** - Added full complex data type support (dict, list, tuple, str, object) with Pydantic 2.x validation
- 013-event-writer-fix: Added Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), aiofiles (async I/O for async mode)
- 012-spatial-maps: Added Python 3.12 + Pydantic 2.x (state models), PyYAML 6.x (config), structlog 24.x (logging), NetworkX (graph algorithms for shortest path)

## Complex Data Type Support (Feature 014)

### Supported Types
1. **dict** - Dynamic keys (`key_type` + `value_type`) or fixed schema mode
2. **list** - Homogeneous collections with `item_type` and optional `max_length`
3. **tuple** - Fixed-length heterogeneous sequences with per-element types
4. **str** - Unrestricted strings with optional regex `pattern` and `max_length`
5. **object** - Nested structures with recursive schema definitions

### Usage Examples

**Dictionary (Inventory System)**:
```yaml
state_variables:
  agent_vars:
    inventory:
      type: dict
      key_type: str
      value_type: float
      default: {}
```

**Tuple (Coordinates)**:
```yaml
state_variables:
  agent_vars:
    location:
      type: tuple
      item_types:
        - type: float
          default: 0.0
        - type: float
          default: 0.0
      default: [0.0, 0.0]
```

**List (Action History)**:
```yaml
state_variables:
  agent_vars:
    action_history:
      type: list
      item_type: str
      max_length: 100
      default: []
```

**Object (Nested Town)**:
```yaml
state_variables:
  global_vars:
    capital:
      type: object
      schema:
        name:
          type: str
          default: "Capital City"
        population:
          type: int
          min: 0
          default: 10000
        position:
          type: tuple
          item_types:
            - type: float
              default: 0.0
            - type: float
              default: 0.0
          default: [0.0, 0.0]
      default:
        name: "Capital City"
        population: 10000
        position: [0.0, 0.0]
```

### Constraints & Limits
- **Dict**: Max 1000 items, max 4 levels nesting depth
- **List**: Max 1000 items (configurable via `max_length`), max 3 levels nesting depth
- **Tuple**: Fixed length defined by `item_types`, per-element type constraints
- **String**: Optional regex `pattern` validation, optional `max_length` constraint
- **Object**: Recursive nesting supported, uses fixed schema definition

### Backward Compatibility
✅ All existing scalar-only configurations work unchanged
✅ 14 scalar type tests pass without modification
✅ No breaking changes to float/int/bool/categorical types

### Test Coverage
- 48 tests for complex types (unit + integration)
- 14 tests for scalar types (backward compatibility)
- config.py: 66% coverage
- state.py: 58% coverage

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
