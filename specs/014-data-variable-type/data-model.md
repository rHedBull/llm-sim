# Data Model: Complex Data Type Support for State Variables

**Feature**: `014-data-variable-type` | **Phase**: 1 - Design | **Date**: 2025-10-13

## Overview

This document specifies the extended `VariableDefinition` data model that adds support for complex data types (dict, list, tuple, str, object) while maintaining backward compatibility with existing scalar types (float, int, bool, categorical).

## Extended VariableDefinition Schema

### Core Fields

```python
class VariableDefinition(BaseModel):
    """Definition of a single state variable with scalar and complex type support."""

    type: Literal["float", "int", "bool", "categorical", "dict", "list", "tuple", "str", "object"]

    # Scalar type fields (existing - unchanged)
    min: Optional[float] = None          # For float/int min constraint
    max: Optional[float] = None          # For float/int max constraint
    values: Optional[List[str]] = None   # For categorical values
    default: Union[float, int, bool, str, dict, list, tuple, None]

    # Complex type fields (new)
    key_type: Optional[Literal["str", "int"]] = None                    # For dict keys
    value_type: Optional[Union[str, "VariableDefinition"]] = None       # For dict values or list items
    item_type: Optional[Union[str, "VariableDefinition"]] = None        # For list item type
    item_types: Optional[List[Union[str, "VariableDefinition"]]] = None # For tuple element types
    schema: Optional[Dict[str, "VariableDefinition"]] = None            # For object/dict fixed schema
    pattern: Optional[str] = None                                       # For str regex validation
    max_length: Optional[int] = None                                    # For str/list length constraint
```

### Type-Specific Configuration

#### Dictionary Type (`type: dict`)

Supports two modes:

**Mode 1: Dynamic Keys (key_type + value_type)**
- Use when keys are not known at configuration time
- `key_type`: Either "str" or "int" for key type
- `value_type`: Type specification for all values (scalar type string or nested VariableDefinition)
- Example: `{type: dict, key_type: str, value_type: float}` for `dict[str, float]`

**Mode 2: Fixed Schema (schema)**
- Use when keys are predefined with individual type constraints
- `schema`: Dictionary mapping field names to their VariableDefinition
- Example: Stats object with known fields (health, mana, stamina)
- Cannot combine with `key_type`/`value_type`

**Validation Rules:**
- Exactly one of (`key_type` + `value_type`) or `schema` must be provided
- `key_type` must be "str" or "int" if specified
- Maximum nesting depth: 4 levels for dict-in-dict
- Maximum collection size: 1000 items per dict
- Default must be empty dict `{}` or conform to schema if fixed schema

#### List Type (`type: list`)

**Required Fields:**
- `item_type`: Type specification for all list items (scalar type string or nested VariableDefinition)

**Optional Fields:**
- `max_length`: Maximum number of items allowed (if specified, must be > 0 and <= 1000)

**Validation Rules:**
- All items must match `item_type` specification
- If `max_length` is specified, validation rejects additions exceeding limit
- Maximum nesting depth: 3 levels for list-in-list
- Maximum collection size: 1000 items if `max_length` not specified
- Default must be empty list `[]` or conform to item_type

#### Tuple Type (`type: tuple`)

**Required Fields:**
- `item_types`: List of type specifications, one per element position

**Per-Element Constraints:**
- Each element in `item_types` can be a scalar type string or nested VariableDefinition
- Per-element min/max constraints supported via nested VariableDefinition
- Example: `[(float, {min: 0, max: 100}), (int, {min: 0}), str]`

**Validation Rules:**
- Fixed length: tuple length must match `len(item_types)`
- Each element validated against corresponding type in `item_types`
- Tuples are immutable in Python but serialize to JSON arrays
- Maximum nesting: tuples can contain dicts/lists (subject to their depth limits)
- Default must be list/tuple with correct length and element types

#### String Type (`type: str`)

**Optional Fields:**
- `pattern`: Regex pattern for validation (Python `re` module syntax)
- `max_length`: Maximum string length (if specified, must be > 0)

**Validation Rules:**
- Unrestricted strings (no predefined values list like categorical)
- `pattern` validation uses `re.match()` (full string match)
- Nullable by default: `Optional[str]` unless default is non-null
- Empty string `""` is valid unless pattern prohibits it
- Default can be `null` or any valid string

#### Object Type (`type: object`)

**Required Fields:**
- `schema`: Dictionary mapping field names to their VariableDefinition

**Validation Rules:**
- Nested validation applied recursively to all schema fields
- All fields in schema are required unless their default is `None`
- Cannot have circular references in schema (detected at config load)
- Maximum total nesting depth across all types: 10 levels
- Default must conform to schema structure

## Validation Rules Summary

### Depth Limits (FR-006a, FR-011a)

| Type | Maximum Nesting Depth | Enforcement Point |
|------|----------------------|-------------------|
| dict | 4 levels | Config load time |
| list | 3 levels | Config load time |
| tuple | No specific limit | Subject to overall depth |
| object | No specific limit | Subject to overall depth |
| Overall | 10 levels total | Config load time |

**Example of dict depth counting:**
```yaml
# Depth 1: dict
inventory: {type: dict, key_type: str, value_type: int}

# Depth 2: dict[str, dict[str, int]]
nested: {type: dict, key_type: str, value_type: {type: dict, key_type: str, value_type: int}}

# Depth 4 (maximum for dict)
deeply_nested:
  type: dict
  key_type: str
  value_type:
    type: dict
    key_type: str
    value_type:
      type: dict
      key_type: str
      value_type:
        type: dict
        key_type: str
        value_type: int
```

### Collection Size Limits (FR-028a, FR-028b)

| Type | Maximum Size | Validation Point |
|------|--------------|------------------|
| dict | 1000 items | Runtime validation |
| list | 1000 items (unless max_length < 1000) | Runtime validation |
| str | 10,000 characters (unless max_length specified) | Runtime validation |

**Error Message Format:**
```
ValidationError: List exceeds maximum size of 1000 items (got 1500 items) at field 'agent_state.history'
```

### Circular Reference Detection (FR-024, FR-024a)

**Detection Algorithm:**
- Depth-First Search (DFS) with recursion stack tracking
- Runs during config load (schema definition phase)
- Detects cycles in object schemas referencing other object schemas

**Error Message Format:**
```
CircularSchemaError: Circular reference detected in schema definitions:
  Cycle: Agent -> Inventory -> Item -> Agent
  Fields: Agent.inventory -> Inventory.items -> Item.owner -> Agent

Suggested fixes:
  1. Use Optional[ForwardRef] for back-references
  2. Use string IDs instead of nested objects
  3. Flatten the schema structure
```

### Type Coercion Behavior

Following Pydantic 2.x semantics:

| Input Type | Target Type | Behavior |
|------------|-------------|----------|
| JSON array | tuple | Coerced to tuple with type validation |
| JSON object | dict | Accepted as-is with validation |
| str | int/float | Coerced if parseable |
| list | tuple | Coerced if lengths match |
| null | Optional[T] | Accepted if field is Optional |

## YAML Configuration Examples

### Dictionary Examples

**Dynamic keys inventory:**
```yaml
state_variables:
  agent_vars:
    inventory:
      type: dict
      key_type: str
      value_type: float
      default: {}
```

**Fixed schema stats:**
```yaml
state_variables:
  agent_vars:
    stats:
      type: dict
      schema:
        health:
          type: float
          min: 0
          max: 100
          default: 100
        mana:
          type: float
          min: 0
          max: 100
          default: 100
        stamina:
          type: int
          min: 0
          max: 10
          default: 10
      default:
        health: 100
        mana: 100
        stamina: 10
```

**Nested dict (towns with inventories):**
```yaml
state_variables:
  global_vars:
    towns:
      type: dict
      key_type: str
      value_type:
        type: dict
        schema:
          population:
            type: int
            min: 0
            default: 1000
          resources:
            type: dict
            key_type: str
            value_type: float
            default: {}
      default: {}
```

### List Examples

**Simple string list:**
```yaml
state_variables:
  agent_vars:
    action_history:
      type: list
      item_type: str
      max_length: 10
      default: []
```

**List of tuples (position history):**
```yaml
state_variables:
  agent_vars:
    position_history:
      type: list
      item_type:
        type: tuple
        item_types: [float, float]
      max_length: 100
      default: []
```

**Nested list (list of lists):**
```yaml
state_variables:
  agent_vars:
    grid_data:
      type: list
      item_type:
        type: list
        item_type: int
      default: []
```

### Tuple Examples

**2D coordinates:**
```yaml
state_variables:
  agent_vars:
    location:
      type: tuple
      item_types: [float, float]
      default: [0.0, 0.0]
```

**RGB color with constraints:**
```yaml
state_variables:
  agent_vars:
    color:
      type: tuple
      item_types:
        - type: int
          min: 0
          max: 255
        - type: int
          min: 0
          max: 255
        - type: int
          min: 0
          max: 255
      default: [255, 255, 255]
```

**Heterogeneous tuple (id, name, coordinates):**
```yaml
state_variables:
  agent_vars:
    entity_data:
      type: tuple
      item_types:
        - int              # ID
        - str              # Name
        - type: tuple      # Coordinates
          item_types: [float, float]
      default: [0, "Unknown", [0.0, 0.0]]
```

### String Examples

**Unrestricted string:**
```yaml
state_variables:
  agent_vars:
    target_destination:
      type: str
      default: null
```

**Pattern-validated string:**
```yaml
state_variables:
  agent_vars:
    agent_name:
      type: str
      pattern: "^[A-Za-z][A-Za-z0-9_]{2,19}$"
      max_length: 20
      default: "Agent_1"
```

**String with length constraint:**
```yaml
state_variables:
  agent_vars:
    notes:
      type: str
      max_length: 500
      default: ""
```

### Object Examples

**Nested object (town structure):**
```yaml
state_variables:
  global_vars:
    capital:
      type: object
      schema:
        name:
          type: str
          default: "Capital City"
        position:
          type: tuple
          item_types: [float, float]
          default: [0.0, 0.0]
        population:
          type: int
          min: 0
          default: 10000
        resources:
          type: dict
          key_type: str
          value_type: float
          default: {}
      default:
        name: "Capital City"
        position: [0.0, 0.0]
        population: 10000
        resources: {}
```

## JSON Serialization Format

### Checkpoint Format

All complex types serialize to standard JSON:

```json
{
  "turn": 5,
  "agents": {
    "Trader_1": {
      "name": "Trader_1",
      "inventory": {"food": 10.5, "metal": 5.0},
      "location": [10.0, 20.0],
      "action_history": ["spawn", "move", "trade"],
      "stats": {"health": 100.0, "mana": 50.0, "stamina": 8}
    }
  },
  "global_state": {
    "towns": {
      "Agriculture Town": {
        "population": 1500,
        "resources": {"food": 1000.0, "wood": 500.0}
      }
    }
  }
}
```

### Tuple Serialization Behavior

**Important**: Tuples serialize as JSON arrays and lose immutability in JSON representation:

- Python: `(1.0, 2.0)` → JSON: `[1.0, 2.0]` → Python: `(1.0, 2.0)`
- Round-trip validation restores tuple type based on annotations
- Immutability is preserved in Python but not in JSON files

**Implications:**
- Users editing checkpoint JSON manually should use arrays for tuple values
- Type safety restored during deserialization via `model_validate_json()`
- Document this behavior in user guide to avoid confusion

### None/Null Handling

Optional fields serialize based on mode:

```python
# mode='json' - includes None as null
{"inventory": null, "location": [0.0, 0.0]}

# exclude_none=True - omits None values
{"location": [0.0, 0.0]}
```

**Default serialization**: Include None as null for explicit state representation

## Implementation Notes

### Type Annotation Generation

The `create_agent_state_model()` and `create_global_state_model()` functions in `state.py` must be extended to handle complex types:

```python
def get_type_annotation(var_def: VariableDefinition) -> type:
    """Convert VariableDefinition to Python type annotation."""
    if var_def.type == "dict":
        if var_def.schema:
            # Fixed schema: create nested model
            return create_nested_model_from_schema(var_def.schema)
        else:
            # Dynamic keys: dict[KeyType, ValueType]
            key_type = str if var_def.key_type == "str" else int
            value_type = get_type_annotation_for_value(var_def.value_type)
            return dict[key_type, value_type]

    elif var_def.type == "list":
        item_type = get_type_annotation_for_value(var_def.item_type)
        return list[item_type]

    elif var_def.type == "tuple":
        element_types = [get_type_annotation_for_value(t) for t in var_def.item_types]
        return tuple[*element_types]

    elif var_def.type == "str":
        return str

    elif var_def.type == "object":
        return create_nested_model_from_schema(var_def.schema)

    # ... existing scalar type handling ...
```

### Validation Performance Strategy

Per research findings (Section 5.1):

1. **Use `model_validate_json()` for JSON input** (30% faster than two-pass)
2. **Enable string caching** for dict-heavy models (`cache_strings='keys'`)
3. **Use concrete types** (`dict`, `list`, `tuple`) not abstract (`Mapping`, `Sequence`)
4. **Prefer 'after' validators** over 'wrap' validators (20% faster)
5. **Cache compiled models** by schema hash to avoid redundant compilation

**Target Performance** (FR-028):
- <10ms for 100 agents × 50 variables with 3 dicts, 2 lists, 1 tuple each
- Expected: ~5ms actual validation time (50% buffer for safety)

### Error Message Format

Following Pydantic 2.x error structure with custom formatting:

```python
def format_validation_error(error: ValidationError) -> str:
    """Format validation error with clear field path."""
    messages = []
    for err in error.errors():
        field_path = loc_to_dot_notation(err['loc'])
        messages.append(f"{field_path}: {err['msg']}")
    return "\n".join(messages)

def loc_to_dot_notation(loc: tuple) -> str:
    """Convert ('agents', 'Trader_1', 'inventory', 'food') to 'agents[Trader_1].inventory.food'"""
    path = ''
    for i, x in enumerate(loc):
        if isinstance(x, str):
            path += '.' if i > 0 else ''
            path += x
        elif isinstance(x, int):
            path += f'[{x}]'
    return path
```

## Backward Compatibility

### Existing Scalar Types

All scalar types remain unchanged:

| Type | Fields | Validation |
|------|--------|------------|
| float | min, max, default | Unchanged |
| int | min, max, default | Unchanged |
| bool | default | Unchanged |
| categorical | values, default | Unchanged |

### Migration Path

**Phase 1: Existing configs work unchanged**
- No changes required to existing YAML configs
- Scalar-only simulations run identically

**Phase 2: Add complex types incrementally**
- Add new complex variables alongside existing scalar variables
- Mix scalar and complex types freely in same config

**Phase 3: Checkpoint compatibility**
- New checkpoints include complex types in JSON
- Old checkpoints (scalar-only) load successfully
- Checkpoint with complex types cannot load on older version (expected)

## Next Steps

This data model serves as the foundation for:

1. **contracts/variable_definition.json** - JSON Schema formal specification
2. **Implementation** - Extend `VariableDefinition`, `create_agent_state_model()`, `create_global_state_model()`
3. **Testing** - Unit tests for each type, validation rules, serialization
4. **Documentation** - User guide (quickstart.md) with examples

---

**Document Status**: Phase 1 Design Complete | Ready for Contract Generation
**Created**: 2025-10-13
**References**: spec.md, research.md, config.py, state.py
