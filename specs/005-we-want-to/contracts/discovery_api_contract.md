# Discovery API Contract

**Component**: `llm_sim.orchestrator.ComponentDiscovery`
**Type**: Service Class
**Purpose**: Dynamically discover and load concrete implementations by filename

## Interface Contract

### Class Definition
```python
from pathlib import Path
from typing import Type, List, Dict

class ComponentDiscovery:
    """Discovers and loads concrete implementations from filesystem."""
```

### Constructor

#### `__init__(self, implementations_root: Path)`
**Purpose**: Initialize discovery service with implementations directory
**Parameters**:
- `implementations_root: Path` - Root directory containing implementations/ subdirectories
**Postconditions**:
- `self.implementations_root` is set
- `self._cache` is initialized as empty dict

### Public Methods

#### `load_agent(filename: str) -> Type[BaseAgent]`
**Purpose**: Load agent implementation by filename
**Parameters**:
- `filename: str` - Python filename without .py extension (e.g., "econ_llm_agent")
**Returns**: `Type[BaseAgent]` - Agent class (not instance)
**Raises**:
- `FileNotFoundError` - If `implementations/agents/{filename}.py` doesn't exist
- `TypeError` - If loaded class doesn't inherit from BaseAgent
- `AttributeError` - If expected class name not found in module
**Behavior**:
- Converts filename to expected class name (snake_case → PascalCase)
- Loads module from `implementations/agents/{filename}.py`
- Extracts class matching expected name
- Validates inheritance from BaseAgent
- Caches loaded class for subsequent calls

**Example**:
```python
discovery = ComponentDiscovery(Path("src/llm_sim"))
AgentClass = discovery.load_agent("econ_llm_agent")  # Returns EconLLMAgent class
agent_instance = AgentClass(name="TestAgent", ...)   # Instantiate
```

#### `load_engine(filename: str) -> Type[BaseEngine]`
**Purpose**: Load engine implementation by filename
**Parameters**:
- `filename: str` - Python filename without .py extension
**Returns**: `Type[BaseEngine]` - Engine class
**Raises**: Same as `load_agent` but validates BaseEngine inheritance
**Behavior**: Same as `load_agent` but for engines directory

#### `load_validator(filename: str) -> Type[BaseValidator]`
**Purpose**: Load validator implementation by filename
**Parameters**:
- `filename: str` - Python filename without .py extension
**Returns**: `Type[BaseValidator]` - Validator class
**Raises**: Same as `load_agent` but validates BaseValidator inheritance
**Behavior**: Same as `load_agent` but for validators directory

#### `list_agents() -> List[str]`
**Purpose**: List all available agent implementations
**Returns**: `List[str]` - Filenames of all .py files in agents/ (without .py extension)
**Behavior**:
- Scans `implementations/agents/` directory
- Returns filenames excluding `__init__.py` and `_*` files
- Sorted alphabetically

#### `list_engines() -> List[str]`
**Purpose**: List all available engine implementations
**Returns**: `List[str]` - Filenames of all engine implementations
**Behavior**: Same as `list_agents` but for engines directory

#### `list_validators() -> List[str]`
**Purpose**: List all available validator implementations
**Returns**: `List[str]` - Filenames of all validator implementations
**Behavior**: Same as `list_agents` but for validators directory

### Private Methods

#### `_filename_to_classname(filename: str) -> str`
**Purpose**: Convert snake_case filename to PascalCase class name
**Parameters**:
- `filename: str` - Snake case filename
**Returns**: `str` - PascalCase class name
**Examples**:
- `"econ_llm_agent"` → `"EconLLMAgent"`
- `"nation"` → `"Nation"`
- `"always_valid"` → `"AlwaysValid"`

#### `_load_module(component_type: str, filename: str) -> ModuleType`
**Purpose**: Dynamically import module from filesystem
**Parameters**:
- `component_type: str` - One of "agents", "engines", "validators"
- `filename: str` - Filename without extension
**Returns**: `ModuleType` - Loaded Python module
**Raises**: `FileNotFoundError` if file doesn't exist

#### `_validate_inheritance(cls: Type, base_class: Type) -> None`
**Purpose**: Verify class inherits from expected base
**Parameters**:
- `cls: Type` - Loaded class to validate
- `base_class: Type` - Expected base class
**Raises**: `TypeError` if inheritance check fails

## Error Messages Contract

### FileNotFoundError
```
No implementation found for '{component_type}' with filename '{filename}'
Expected file: {expected_path}
Available {component_type}: {list_of_available}
```

### TypeError
```
Class '{classname}' from '{filename}' does not inherit from {base_class}
Expected: class {classname}({base_class.__name__})
Found: class {classname}({actual_bases})
```

### AttributeError
```
Module '{filename}' does not contain expected class '{expected_classname}'
Available classes in module: {available_classes}
Hint: Filename 'foo_bar.py' should contain class 'FooBar'
```

## Performance Contract

### Caching Behavior
- First call to `load_*` loads module and caches class
- Subsequent calls return cached class (O(1) lookup)
- Cache never expires (implementations don't change at runtime)
- Memory overhead: ~1KB per cached class (acceptable for <100 implementations)

### Performance Targets
- First load: <50ms (includes filesystem access, import, validation)
- Cached load: <1ms (dict lookup)
- List operations: <10ms (directory scan)

## Thread Safety

**Not thread-safe by design** - Discovery happens during orchestrator initialization (single-threaded).
If concurrent access needed in future, add locking around cache.

## Integration with Orchestrator

### Usage in Configuration Loading
```python
# orchestrator.py
def from_yaml(cls, config_path: str) -> SimulationOrchestrator:
    config = yaml.safe_load(Path(config_path).read_text())

    discovery = ComponentDiscovery(Path(__file__).parent)

    # Load engine
    EngineClass = discovery.load_engine(config["engine"]["type"])
    engine = EngineClass(config)

    # Load validator
    ValidatorClass = discovery.load_validator(config["validator"]["type"])
    validator = ValidatorClass(...)

    # Load agents
    agents = []
    for agent_config in config["agents"]:
        AgentClass = discovery.load_agent(agent_config["type"])
        agents.append(AgentClass(name=agent_config["name"], ...))

    return cls(config=config, engine=engine, validator=validator, agents=agents)
```

## Validation Tests

Contract tests MUST verify:
1. `load_agent` returns class that inherits from BaseAgent
2. `load_agent` caches results
3. `load_agent` raises FileNotFoundError for missing files
4. `load_agent` raises TypeError for invalid inheritance
5. `load_agent` raises AttributeError for name mismatches
6. `list_agents` returns all .py files (excluding __init__ and _*)
7. Error messages include helpful context
8. Filename-to-classname conversion works correctly

## Breaking Changes

Changes to this API are BREAKING:
- Changing method signatures
- Changing exception types raised
- Changing filename-to-classname conversion logic (breaks existing files)
- Removing public methods

## Non-Breaking Changes

These changes are NON-BREAKING:
- Adding new load_* methods for new component types
- Improving error messages
- Performance optimizations
- Adding optional parameters with defaults
