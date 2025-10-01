# Data Model: Abstract Agent and Global State System

**Feature**: Dynamic variable system for simulation state
**Date**: 2025-10-01
**Status**: Complete

## Overview
This document defines the data entities for the abstract variable system, including configuration models for variable definitions and runtime state models with dynamic fields.

---

## Entity: VariableDefinition

**Purpose**: Describes a single state variable definition from YAML configuration

**Location**: `src/llm_sim/models/config.py` (new model)

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `type` | Literal["float", "int", "bool", "categorical"] | Required | Variable data type |
| `min` | Optional[float] | Only for float/int types | Minimum allowed value (inclusive) |
| `max` | Optional[float] | Only for float/int types | Maximum allowed value (inclusive) |
| `values` | Optional[List[str]] | Required for categorical type | Allowed categorical values |
| `default` | Union[float, int, bool, str] | Required | Default/initial value for the variable |

**Validation Rules**:
- `type` must be one of the four supported types
- For `float`/`int`: `min` ≤ `default` ≤ `max` (if min/max specified)
- For `categorical`: `default` must be in `values` list
- For `categorical`: `values` list must be non-empty
- `min` < `max` (if both specified)

**Example**:
```python
# Float with constraints
VariableDefinition(
    type="float",
    min=0.0,
    max=1000000.0,
    default=1000.0
)

# Categorical
VariableDefinition(
    type="categorical",
    values=["bronze", "iron", "steel"],
    default="bronze"
)

# Boolean
VariableDefinition(
    type="bool",
    default=True
)
```

**Relationships**:
- Referenced by `StateVariablesConfig.agent_vars` (dict mapping)
- Referenced by `StateVariablesConfig.global_vars` (dict mapping)
- Used to generate Pydantic models for `AgentState` and `GlobalState`

---

## Entity: StateVariablesConfig

**Purpose**: Container for all variable definitions (agent and global)

**Location**: `src/llm_sim/models/config.py` (new model)

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `agent_vars` | Dict[str, VariableDefinition] | Keys are variable names | Agent state variable definitions |
| `global_vars` | Dict[str, VariableDefinition] | Keys are variable names | Global state variable definitions |

**Validation Rules**:
- Variable names must be valid Python identifiers
- Variable names must not conflict with reserved names: `name` (for AgentState), `turn`, `agents`, `global_state`, `reasoning_chains` (for SimulationState)
- No duplicate variable names within agent_vars or global_vars

**Example**:
```python
StateVariablesConfig(
    agent_vars={
        "gdp": VariableDefinition(type="float", min=0, default=1000.0),
        "population": VariableDefinition(type="int", min=1, default=1000000)
    },
    global_vars={
        "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.02),
        "open_economy": VariableDefinition(type="bool", default=True)
    }
)
```

**Relationships**:
- Owned by `SimulationConfig.state_variables`
- Drives creation of dynamic `AgentState` and `GlobalState` models

---

## Entity: SimulationConfig (Modified)

**Purpose**: Extended to include state variable definitions

**Location**: `src/llm_sim/models/config.py` (modify existing)

**New Attribute**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `state_variables` | Optional[StateVariablesConfig] | None for backward compatibility | Variable definitions for this simulation |

**Backward Compatibility**:
- When `state_variables` is None, use implicit default variables:
  - Agent vars: `{"economic_strength": {type: float, min: 0, default: 0}}`
  - Global vars: `{"interest_rate": {type: float, default: 0.05}, "total_economic_value": {type: float, default: 0}, ...}`
- Log deprecation warning when defaults are used

**Example**:
```yaml
# New-style config
simulation:
  name: "Custom Sim"
  max_turns: 100

state_variables:
  agent_vars:
    gdp:
      type: float
      min: 0
      default: 1000.0
  global_vars:
    inflation:
      type: float
      default: 0.02
```

---

## Entity: AgentState (Modified - Dynamic)

**Purpose**: State of an individual agent with configurable variables

**Location**: `src/llm_sim/models/state.py` (modify existing)

**Change**: Convert from static Pydantic model to dynamically generated model

**Fixed Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | str | Required | Agent identifier (unique within simulation) |

**Dynamic Attributes**:
- Fields are created at runtime based on `StateVariablesConfig.agent_vars`
- Each variable in config becomes a field with:
  - Type: float, int, bool, or Literal[...] (for categorical)
  - Constraints: Field(ge=min, le=max) for numeric types
  - Default: From VariableDefinition.default

**Creation Pattern**:
```python
def create_agent_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]:
    """Generate AgentState model from variable definitions."""
    fields = {'name': (str, ...)}  # Required field

    for var_name, var_def in var_defs.items():
        if var_def.type == "float":
            fields[var_name] = (
                float,
                Field(ge=var_def.min, le=var_def.max, default=var_def.default)
            )
        elif var_def.type == "int":
            fields[var_name] = (
                int,
                Field(ge=var_def.min, le=var_def.max, default=var_def.default)
            )
        elif var_def.type == "bool":
            fields[var_name] = (bool, Field(default=var_def.default))
        elif var_def.type == "categorical":
            fields[var_name] = (
                Literal[tuple(var_def.values)],
                Field(default=var_def.default)
            )

    return create_model(
        'AgentState',
        __config__=ConfigDict(frozen=True),
        **fields
    )
```

**Example Instance** (for economic simulation):
```python
agent = AgentState(
    name="Nation_A",
    gdp=1000.0,
    population=1000000
)
```

**State Updates**:
- Frozen model → updates via `model_copy(update={...})`
- Validation triggered automatically on copy
- ValidationError raised if constraints violated

**Relationships**:
- Created by factory function from `StateVariablesConfig.agent_vars`
- Instances stored in `SimulationState.agents` dict
- Serialized to checkpoint files

---

## Entity: GlobalState (Modified - Dynamic)

**Purpose**: World-level state with configurable variables

**Location**: `src/llm_sim/models/state.py` (modify existing)

**Change**: Convert from static Pydantic model to dynamically generated model

**Dynamic Attributes**:
- All fields are created at runtime based on `StateVariablesConfig.global_vars`
- No fixed fields (unlike AgentState which has `name`)
- Field types and constraints same as AgentState

**Creation Pattern**:
```python
def create_global_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]:
    """Generate GlobalState model from variable definitions."""
    fields = {}

    for var_name, var_def in var_defs.items():
        # Same logic as create_agent_state_model
        ...

    return create_model(
        'GlobalState',
        __config__=ConfigDict(frozen=True),
        **fields
    )
```

**Example Instance** (for economic simulation):
```python
global_state = GlobalState(
    inflation=0.02,
    open_economy=True,
    interest_rate=0.05
)
```

**Relationships**:
- Created by factory function from `StateVariablesConfig.global_vars`
- Single instance per simulation stored in `SimulationState.global_state`
- Serialized to checkpoint files

---

## Entity: SimulationState (Modified)

**Purpose**: Complete simulation state at a point in time

**Location**: `src/llm_sim/models/state.py` (modify existing)

**Attributes** (unchanged structure, dynamic content):

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `turn` | int | ≥ 0 | Current turn number |
| `agents` | Dict[str, AgentState] | Keys match agent names | Agent states (dynamic model) |
| `global_state` | GlobalState | Required | Global state (dynamic model) |
| `reasoning_chains` | List[LLMReasoningChain] | Default=[] | LLM reasoning history (existing) |

**Changes**:
- `AgentState` and `GlobalState` are now dynamically generated types
- Structure remains the same, but field composition varies per simulation
- Serialization/deserialization works transparently (Pydantic handles it)

**Relationships**:
- Contains one `GlobalState` instance
- Contains multiple `AgentState` instances
- Serialized to/from checkpoint files
- Checkpoint metadata includes schema hash for compatibility validation

---

## Entity: CheckpointMetadata (Modified)

**Purpose**: Metadata for checkpoint files, extended with schema information

**Location**: `src/llm_sim/models/checkpoint.py` (modify existing)

**New Attribute**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `schema_hash` | str | 64-char hex (SHA-256) | Hash of variable definitions for compatibility checking |

**Schema Hash Computation**:
```python
def compute_schema_hash(
    agent_vars: Dict[str, VariableDefinition],
    global_vars: Dict[str, VariableDefinition]
) -> str:
    """Compute deterministic hash of variable schema."""
    schema = {
        'agent_vars': {
            name: {
                'type': vd.type,
                'min': vd.min,
                'max': vd.max,
                'values': vd.values
            }
            for name, vd in sorted(agent_vars.items())
        },
        'global_vars': {
            name: {
                'type': vd.type,
                'min': vd.min,
                'max': vd.max,
                'values': vd.values
            }
            for name, vd in sorted(global_vars.items())
        }
    }
    schema_json = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(schema_json.encode()).hexdigest()
```

**Usage**:
- Computed when checkpoint is created
- Stored in checkpoint file metadata
- Validated when checkpoint is loaded
- Mismatch → SchemaCompatibilityError (reject load)

**Relationships**:
- Part of checkpoint file structure
- Used by `CheckpointManager` for validation

---

## Data Flow

```
YAML Config
    ↓
SimulationConfig.state_variables: StateVariablesConfig
    ↓
    ├─→ agent_vars: Dict[str, VariableDefinition]
    │       ↓
    │   create_agent_state_model() → AgentState (dynamic Pydantic model)
    │       ↓
    │   SimulationState.agents: Dict[str, AgentState instances]
    │
    └─→ global_vars: Dict[str, VariableDefinition]
            ↓
        create_global_state_model() → GlobalState (dynamic Pydantic model)
            ↓
        SimulationState.global_state: GlobalState instance

Checkpoint Save:
    SimulationState
        ↓
    compute_schema_hash(agent_vars, global_vars)
        ↓
    CheckpointMetadata(schema_hash=...)
        ↓
    JSON file with state + metadata

Checkpoint Load:
    JSON file
        ↓
    Extract metadata.schema_hash
        ↓
    Compute current schema hash from config
        ↓
    Compare hashes
        ↓ (mismatch)
    SchemaCompatibilityError (reject load)
        ↓ (match)
    Deserialize SimulationState
        ↓
    Validate all fields (Pydantic validation)
```

---

## Validation Summary

### Config-Time Validation
1. **Variable definitions**:
   - Type is supported
   - min < max (if both specified)
   - default within [min, max] (numeric types)
   - default in values list (categorical)
   - values list non-empty (categorical)

2. **Variable names**:
   - Valid Python identifiers
   - No reserved name conflicts
   - No duplicates

### Runtime Validation
1. **State initialization**:
   - All defaults satisfy constraints
   - Required fields present

2. **State updates**:
   - New values satisfy type constraints
   - New values within min/max bounds
   - Categorical values in allowed list

### Checkpoint Validation
1. **Save**:
   - Schema hash computed
   - All state serializable

2. **Load**:
   - Schema hash matches current config
   - All fields deserialize correctly
   - All values satisfy constraints

---

## Implementation Notes

1. **Module Organization**:
   - Config models: `src/llm_sim/models/config.py`
   - State models: `src/llm_sim/models/state.py`
   - Model factories: `src/llm_sim/models/state.py` (new functions)
   - Checkpoint models: `src/llm_sim/models/checkpoint.py`

2. **Factory Functions**:
   - `create_agent_state_model(var_defs) -> Type[BaseModel]`
   - `create_global_state_model(var_defs) -> Type[BaseModel]`
   - Cache created models to avoid regeneration

3. **Error Types**:
   - `ConfigValidationError`: Invalid variable definitions
   - `SchemaCompatibilityError`: Checkpoint schema mismatch
   - `pydantic.ValidationError`: Constraint violations

4. **Backward Compatibility**:
   - Detect missing `state_variables` in config
   - Use default variable definitions
   - Log deprecation warning
   - Maintain existing checkpoint format compatibility

---

## Testing Strategy

### Unit Tests
- Variable definition validation
- Model creation from definitions
- Constraint enforcement (min/max, categorical)
- Schema hash computation (deterministic, order-independent)
- Default variable mapping (backward compat)

### Integration Tests
- Full config → state initialization
- State updates with validation
- Checkpoint save/load round-trip
- Schema compatibility rejection

### Contract Tests
- Config YAML schema validation
- Checkpoint JSON schema validation

---

*Data model complete - ready for contract generation*
