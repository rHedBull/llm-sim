# Data Model: Partial Observability

**Feature**: 008-partial-observability-agents
**Date**: 2025-10-02

## Entity Relationship Overview

```
SimulationConfig
    ├── simulation: SimulationSettings
    ├── engine: EngineConfig
    ├── agents: List[AgentConfig]
    ├── validator: ValidatorConfig
    ├── state_variables: StateVariablesConfig
    └── observability: ObservabilityConfig (NEW)
            ├── enabled: bool
            ├── variable_visibility: VariableVisibilityConfig (NEW)
            │       ├── external: List[str]
            │       └── internal: List[str]
            ├── matrix: List[ObservabilityEntry] (NEW)
            │       └── [observer, target, level, noise]
            └── default: DefaultObservability (NEW)
                    ├── level: ObservabilityLevel
                    └── noise: float

SimulationState
    ├── turn: int
    ├── agents: Dict[str, DynamicAgentState]  # Ground truth
    ├── global_state: DynamicGlobalState      # Ground truth
    └── reasoning_chains: List[LLMReasoningChain]

# Observations (NEW - same structure as SimulationState but filtered)
ObservationState = SimulationState
    ├── turn: int (unchanged)
    ├── agents: Dict[str, DynamicAgentState]  # Filtered subset
    ├── global_state: DynamicGlobalState      # Filtered variables
    └── reasoning_chains: []                   # Empty for observations
```

## New Entities

### 1. ObservabilityLevel (Enum)

**Purpose**: Define the three levels of observability

**Fields**:
- `UNAWARE = "unaware"` - Target is invisible
- `EXTERNAL = "external"` - Only public variables visible
- `INSIDER = "insider"` - All variables visible

**Validation Rules**:
- Must be one of the three literal values
- Case-sensitive string matching in YAML

**Usage**:
```python
from enum import Enum

class ObservabilityLevel(str, Enum):
    UNAWARE = "unaware"
    EXTERNAL = "external"
    INSIDER = "insider"
```

---

### 2. VariableVisibilityConfig (Pydantic Model)

**Purpose**: Classify state variables as external (public) or internal (private)

**Fields**:
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `external` | `List[str]` | Yes | Non-empty | List of public variable names |
| `internal` | `List[str]` | Yes | Can be empty | List of private variable names |

**Validation Rules**:
- No overlap between external and internal lists
- All variable names must exist in agent_vars or global_vars (validated by ObservabilityConfig)
- Variables not listed default to external (backward compatibility)

**Example**:
```yaml
variable_visibility:
  external: [economic_strength, position]
  internal: [secret_reserves, hidden_strategy]
```

---

### 3. ObservabilityEntry (Pydantic Model)

**Purpose**: Define observability relationship between one observer and one target

**Fields**:
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `observer` | `str` | Yes | Must be valid agent name | Who is observing |
| `target` | `str` | Yes | Valid agent name or "global" | What is being observed |
| `level` | `ObservabilityLevel` | Yes | Enum value | Observability level |
| `noise` | `float \| None` | Yes | >= 0.0 if not None | Noise factor (None for unaware) |

**Validation Rules**:
- `observer` must be in agents list
- `target` must be in agents list OR equal to "global"
- `noise` must be >= 0.0 or None
- If `level == UNAWARE`, noise should be None (not enforced, just ignored)

**YAML Format**:
```yaml
matrix:
  - [Agent1, Agent2, external, 0.2]   # List format (compact)
  - [Agent1, global, insider, 0.0]
```

**Pydantic Representation**:
```python
class ObservabilityEntry(BaseModel):
    observer: str
    target: str
    level: ObservabilityLevel
    noise: float | None

    @field_validator("noise")
    @classmethod
    def validate_noise(cls, v: float | None) -> float | None:
        if v is not None and v < 0.0:
            raise ValueError("noise must be >= 0.0")
        return v
```

---

### 4. DefaultObservability (Pydantic Model)

**Purpose**: Fallback observability for observer-target pairs not in matrix

**Fields**:
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `level` | `ObservabilityLevel` | Yes | Enum value | Default observability level |
| `noise` | `float` | Yes | >= 0.0 | Default noise factor |

**Validation Rules**:
- `noise` >= 0.0

**Example**:
```yaml
default:
  level: external
  noise: 0.1
```

---

### 5. ObservabilityConfig (Pydantic Model)

**Purpose**: Complete observability configuration for simulation

**Fields**:
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `enabled` | `bool` | Yes | - | Enable/disable observability |
| `variable_visibility` | `VariableVisibilityConfig` | Yes | - | Variable classification |
| `matrix` | `List[ObservabilityEntry]` | Yes | - | Observer-target relationships |
| `default` | `DefaultObservability` | No | - | Fallback for undefined pairs |

**Validation Rules**:
- All `observer` IDs in matrix must be in agents list
- All `target` IDs must be in agents list OR equal to "global"
- All variables in `variable_visibility` lists must exist in `state_variables.agent_vars` or `state_variables.global_vars`
- No duplicate (observer, target) pairs in matrix

**Cross-Entity Validation** (custom validator):
```python
@model_validator(mode="after")
def validate_observability_config(self, info: ValidationInfo) -> "ObservabilityConfig":
    # Get agent names and variable names from parent SimulationConfig context
    context = info.context or {}
    agent_names = context.get("agent_names", [])
    agent_var_names = context.get("agent_var_names", [])
    global_var_names = context.get("global_var_names", [])

    # Validate observers and targets
    for entry in self.matrix:
        if entry.observer not in agent_names:
            raise ValueError(f"Unknown observer '{entry.observer}' in observability matrix")
        if entry.target != "global" and entry.target not in agent_names:
            raise ValueError(f"Unknown target '{entry.target}' in observability matrix")

    # Validate variable names
    all_var_names = set(agent_var_names) | set(global_var_names)
    for var_name in self.variable_visibility.external:
        if var_name not in all_var_names:
            raise ValueError(f"Unknown variable '{var_name}' in external list")
    for var_name in self.variable_visibility.internal:
        if var_name not in all_var_names:
            raise ValueError(f"Unknown variable '{var_name}' in internal list")

    return self
```

**Example**:
```yaml
observability:
  enabled: true
  variable_visibility:
    external: [economic_strength]
    internal: [secret_reserves]
  matrix:
    - [Agent1, Agent1, insider, 0.0]
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, global, external, 0.1]
  default:
    level: unaware
    noise: 0.0
```

---

## Modified Entities

### SimulationConfig (Extended)

**New Field**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `observability` | `ObservabilityConfig \| None` | No | None | Observability configuration |

**Backward Compatibility**:
- If `observability` is `None`, full observability is provided (existing behavior)
- If `observability.enabled == False`, full observability is provided
- Only when `observability.enabled == True` is partial observability applied

---

### VariableDefinition (Extended - Future Enhancement)

*Note: Not implemented in Phase 0, but planned for cleaner config structure*

**Potential New Field** (deferred):
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `visibility` | `Literal["external", "internal"]` | No | "external" | Variable visibility classification |

**Rationale for deferral**:
- Current approach uses separate `variable_visibility` config section
- Adding field to VariableDefinition requires config migration
- Deferred to avoid scope creep in Phase 0

---

## State Models (Unchanged)

### SimulationState

**No structural changes needed**. Observations are represented using the same `SimulationState` model but with:
- Filtered `agents` dict (unaware targets excluded)
- Filtered variables in agent states (internal variables excluded for external observers)
- Filtered `global_state` variables
- Empty `reasoning_chains` (observations don't include others' reasoning)

**Construction Pattern**:
```python
def construct_observation(
    observer_id: str,
    ground_truth: SimulationState,
    config: ObservabilityConfig
) -> SimulationState:
    # Returns new SimulationState with filtered/noisy data
    pass
```

---

## Data Flow

### Configuration Loading
```
YAML File
    ↓
load_config() → SimulationConfig (with validation)
    ↓
Orchestrator initialization
    ↓
Store observability_config for turn loop
```

### Observation Construction
```
Ground Truth SimulationState
    ↓
For each agent (observer):
    ↓
construct_observation(observer_id, ground_truth, config)
    ├── Look up (observer, target) in matrix for each target
    ├── Filter agents dict (exclude unaware)
    ├── Filter variables (external vs internal)
    ├── Apply noise to visible variables
    └── Return new SimulationState
    ↓
Pass observation to agent.decide_action()
```

### Matrix Lookup
```
(observer, target) pair
    ↓
ObservabilityMatrix.get_observability(observer, target)
    ├── Check self._matrix dict
    ├── If found: return (level, noise)
    └── If not found: return (default.level, default.noise)
    ↓
(ObservabilityLevel, noise_factor)
```

---

## Storage Schema

### Configuration (YAML)

```yaml
observability:
  enabled: true
  variable_visibility:
    external: [var1, var2]
    internal: [var3, var4]
  matrix:
    - [observer, target, level, noise]
    - [Agent1, Agent2, external, 0.2]
    - [Agent2, global, insider, 0.0]
  default:
    level: unaware
    noise: 0.0
```

### Runtime (Python)

**ObservabilityMatrix** (internal data structure):
```python
class ObservabilityMatrix:
    _matrix: Dict[Tuple[str, str], Tuple[ObservabilityLevel, float]]
    _default: Tuple[ObservabilityLevel, float]
```

---

## Validation Summary

| Entity | Validation Rules | Error Messages |
|--------|------------------|----------------|
| ObservabilityLevel | Must be unaware/external/insider | "Invalid observability level '{value}'" |
| VariableVisibilityConfig | No overlap, non-empty external | "Variables cannot be both external and internal: {overlap}" |
| ObservabilityEntry | Valid IDs, noise >= 0 | "Unknown observer '{name}'" / "Noise must be >= 0" |
| DefaultObservability | noise >= 0 | "Default noise must be >= 0" |
| ObservabilityConfig | Cross-reference validation | "Unknown variable '{name}' in visibility list" / "Unknown agent '{name}' in matrix" |

---

*Data model complete. All entities defined with validation rules. Ready for contract generation.*
