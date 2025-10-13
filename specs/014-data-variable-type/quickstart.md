# Quickstart: Complex Data Types in llm_sim

**Feature**: Complex Data Type Support | **For Users** | **Updated**: 2025-10-13

## Introduction

llm_sim now supports complex data types for state variables, allowing you to model richer simulations with inventories, coordinates, histories, and nested structures. This guide shows you how to use dictionaries, lists, tuples, strings, and objects in your simulation configs.

## Supported Types

### Scalar Types (Existing)
- `float` - Floating point numbers with min/max constraints
- `int` - Integer numbers with min/max constraints
- `bool` - True/False values
- `categorical` - Predefined set of string values

### Complex Types (New)
- `dict` - Key-value mappings (inventories, resources, stats)
- `list` - Ordered sequences (histories, paths, collections)
- `tuple` - Fixed-length immutable sequences (coordinates, RGB colors)
- `str` - Unrestricted strings with optional pattern validation
- `object` - Nested structures with defined schemas

## Quick Examples

### Dictionary: Agent Inventory

Track items with dynamic keys:

```yaml
state_variables:
  agent_vars:
    inventory:
      type: dict
      key_type: str          # Item names are strings
      value_type: float      # Quantities are floats
      default: {}            # Start with empty inventory
```

**Usage in simulation:**
```json
{
  "name": "Trader_1",
  "inventory": {
    "food": 10.5,
    "metal": 5.0,
    "wood": 20.0
  }
}
```

### Dictionary: Fixed Schema Stats

Define known fields with individual constraints:

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
          default: 50
        stamina:
          type: int
          min: 0
          max: 10
          default: 10
      default:
        health: 100
        mana: 50
        stamina: 10
```

**Usage in simulation:**
```json
{
  "name": "Hero",
  "stats": {
    "health": 75.0,
    "mana": 30.0,
    "stamina": 7
  }
}
```

### List: Action History

Track recent actions with a length limit:

```yaml
state_variables:
  agent_vars:
    action_history:
      type: list
      item_type: str         # Each action is a string
      max_length: 10         # Keep last 10 actions only
      default: []
```

**Usage in simulation:**
```json
{
  "name": "Agent_1",
  "action_history": ["spawn", "move_north", "gather", "trade", "move_south"]
}
```

### Tuple: 2D Coordinates

Model agent positions with fixed-length tuples:

```yaml
state_variables:
  agent_vars:
    location:
      type: tuple
      item_types: [float, float]  # (x, y) coordinates
      default: [0.0, 0.0]
```

**Usage in simulation:**
```json
{
  "name": "Explorer",
  "location": [10.5, 20.3]
}
```

**Important**: Tuples are immutable in Python but serialize as JSON arrays. When loading from JSON, llm_sim automatically restores them as tuples.

### String: Destination Names

Use unrestricted strings for dynamic values:

```yaml
state_variables:
  agent_vars:
    target_destination:
      type: str
      default: null          # Can be null initially
```

**Usage in simulation:**
```json
{
  "name": "Traveler",
  "target_destination": "Market Square"
}
```

### String: Pattern Validation

Enforce naming conventions with regex patterns:

```yaml
state_variables:
  agent_vars:
    agent_id:
      type: str
      pattern: "^AGENT_[0-9]{4}$"  # Must match format AGENT_0001
      max_length: 10
      default: "AGENT_0001"
```

**Valid values:** `AGENT_0001`, `AGENT_9999`
**Invalid values:** `Agent_1`, `AGENT_`, `AGENT_12` (wrong length)

### Object: Nested Town Structure

Define complex nested structures:

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

**Usage in simulation:**
```json
{
  "capital": {
    "name": "Capital City",
    "position": [50.0, 50.0],
    "population": 15000,
    "resources": {
      "food": 5000.0,
      "gold": 1000.0
    }
  }
}
```

## Complete Example: Trading Simulation

Here's a complete config for a trading simulation with agents that have inventories, locations, and track action histories:

```yaml
simulation:
  name: "Trading World"
  max_turns: 100
  checkpoint_interval: 10

engine:
  type: simple_economic

agents:
  - name: Trader_1
    type: trader
    initial_location: Town_A
  - name: Trader_2
    type: trader
    initial_location: Town_B

state_variables:
  agent_vars:
    # Complex types
    inventory:
      type: dict
      key_type: str
      value_type: float
      default: {}

    location:
      type: tuple
      item_types: [float, float]
      default: [0.0, 0.0]

    action_history:
      type: list
      item_type: str
      max_length: 10
      default: []

    target_town:
      type: str
      default: null

    # Scalar types (existing)
    wealth:
      type: float
      min: 0
      default: 100.0

    strategy:
      type: categorical
      values: ["aggressive", "conservative", "balanced"]
      default: "balanced"

  global_vars:
    # Nested dict: towns with resources
    towns:
      type: dict
      key_type: str
      value_type:
        type: object
        schema:
          position:
            type: tuple
            item_types: [float, float]
            default: [0.0, 0.0]
          inventory:
            type: dict
            key_type: str
            value_type: float
            default: {}
          prices:
            type: dict
            key_type: str
            value_type: float
            default: {}
      default: {}

    # Scalar global state
    total_wealth:
      type: float
      default: 0.0

validator:
  type: llm_validator
  domain: trading

llm:
  model: "gemma:3"
  host: "http://localhost:11434"
```

**Initial state for Trader_1:**
```json
{
  "name": "Trader_1",
  "inventory": {"food": 10.0, "tools": 5.0},
  "location": [10.0, 20.0],
  "action_history": ["spawn"],
  "target_town": "Town_B",
  "wealth": 100.0,
  "strategy": "balanced"
}
```

## Nesting and Limits

### Nesting Depth Limits

To maintain performance, llm_sim enforces maximum nesting depths:

| Type | Maximum Depth |
|------|---------------|
| dict | 4 levels |
| list | 3 levels |
| Overall | 10 levels total |

**Example - Maximum dict nesting:**
```yaml
# Level 1: dict
# Level 2: dict[str, dict]
# Level 3: dict[str, dict[str, dict]]
# Level 4: dict[str, dict[str, dict[str, dict]]]
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
        value_type: float  # Level 4 - maximum allowed
```

**Error if exceeded:**
```
DepthLimitError: Nesting depth exceeds limit for dict at 'deeply_nested': 5 > 4
```

### Collection Size Limits

Maximum sizes are enforced at validation time:

- **Dictionaries**: 1000 items max
- **Lists**: 1000 items max (or `max_length` if specified)
- **Strings**: 10,000 characters max (or `max_length` if specified)

**Error if exceeded:**
```
ValidationError: List exceeds maximum size of 1000 items (got 1500) at field 'agent_state.action_history'
```

## Understanding Validation Errors

### Field Path Format

Validation errors show the exact location of the problem using dot notation:

```
agents[Trader_1].inventory.food: Input should be a valid float
global_state.towns[Town_A].position[0]: Input should be less than or equal to 100
```

**Format rules:**
- Object fields: `object.field`
- Dict entries: `dict[key]`
- List items: `list[0]`
- Tuple elements: `tuple[1]`

### Common Errors and Fixes

#### Error: "Categorical type requires 'values' field"

**Cause:** Forgot to specify allowed values for categorical type

**Fix:**
```yaml
# Wrong
strategy:
  type: categorical
  default: "balanced"

# Correct
strategy:
  type: categorical
  values: ["aggressive", "conservative", "balanced"]
  default: "balanced"
```

#### Error: "Dict type requires either (key_type + value_type) or schema"

**Cause:** Missing required fields for dict configuration

**Fix:**
```yaml
# Wrong
inventory:
  type: dict
  default: {}

# Correct (dynamic keys)
inventory:
  type: dict
  key_type: str
  value_type: float
  default: {}

# OR Correct (fixed schema)
stats:
  type: dict
  schema:
    health: {type: float, default: 100}
  default: {health: 100}
```

#### Error: "Tuple length must match item_types length"

**Cause:** Default value has wrong number of elements

**Fix:**
```yaml
# Wrong
location:
  type: tuple
  item_types: [float, float]
  default: [0.0]  # Only 1 element, needs 2

# Correct
location:
  type: tuple
  item_types: [float, float]
  default: [0.0, 0.0]
```

#### Error: "List exceeds maximum length of 10"

**Cause:** Trying to add more items than `max_length` allows

**Fix:** Either increase `max_length` or remove oldest items before adding new ones:

```yaml
# Increase limit
action_history:
  type: list
  item_type: str
  max_length: 20  # Increased from 10
  default: []

# OR: Implement FIFO logic in your simulation to remove old items
```

#### Error: "Pattern validation failed"

**Cause:** String doesn't match the specified regex pattern

**Fix:**
```yaml
agent_id:
  type: str
  pattern: "^AGENT_[0-9]{4}$"  # Requires AGENT_0001 format
  default: "AGENT_0001"

# Valid: "AGENT_0001", "AGENT_9999"
# Invalid: "Agent_1", "AGENT_", "agent_0001" (lowercase)
```

## Tuple Serialization Behavior

**Important**: JSON does not have a tuple type. Tuples serialize as arrays:

```python
# In Python/simulation
location = (10.0, 20.0)  # tuple

# In checkpoint JSON
"location": [10.0, 20.0]  # array

# When loading checkpoint
location = (10.0, 20.0)  # restored as tuple
```

**What this means:**
- Tuples are immutable in your Python simulation code
- Checkpoint JSON files show tuples as arrays
- When loading, llm_sim restores correct types based on your config
- You can edit checkpoint JSON using arrays for tuple values

## Mixing Scalar and Complex Types

You can freely mix scalar and complex types in the same config:

```yaml
state_variables:
  agent_vars:
    # Scalar types
    health: {type: float, min: 0, max: 100, default: 100}
    is_active: {type: bool, default: true}
    role: {type: categorical, values: ["worker", "trader"], default: "worker"}

    # Complex types
    inventory: {type: dict, key_type: str, value_type: float, default: {}}
    location: {type: tuple, item_types: [float, float], default: [0.0, 0.0]}
    history: {type: list, item_type: str, max_length: 10, default: []}
```

## Backward Compatibility

Existing configs with only scalar types work without modification:

```yaml
# Old config (still works)
state_variables:
  agent_vars:
    economic_strength: {type: float, min: 0, default: 0.0}
  global_vars:
    interest_rate: {type: float, default: 0.05}
```

Old checkpoint files load successfully. New checkpoints with complex types require the updated llm_sim version.

## Performance Notes

- Validation is fast: <10ms for 100 agents with complex state
- Large collections (approaching 1000 items) may slow validation
- Deeply nested structures (3+ levels) have slight overhead
- Use `max_length` constraints to prevent unbounded growth

## Next Steps

- **Full documentation**: See `data-model.md` for complete technical specification
- **Examples**: Check `examples/trading_simulation.yaml` for more patterns
- **API Reference**: See JSON Schema in `contracts/variable_definition.json`

---

**Questions?** Check the documentation or file an issue with reproduction details.

**Document Version**: 1.0 | **Feature**: 014-data-variable-type | **Date**: 2025-10-13
