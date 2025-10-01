# Quickstart: Abstract Agent and Global State System

**Feature**: Dynamic variable system for simulation state
**Date**: 2025-10-01
**Audience**: Developers implementing or using the abstract state system

## Overview
This guide demonstrates how to create a custom simulation using the new abstract state variable system. You'll learn how to define your own variables, run a simulation, and verify the results.

---

## Prerequisites
- Python 3.12+
- llm_sim package installed
- Basic understanding of YAML syntax
- Familiarity with simulation concepts (agents, global state)

---

## Example: Military Technology Simulation

We'll create a military simulation that tracks different variables than the default economic simulation:

**Agent Variables**:
- `tech_level`: categorical (stone, bronze, iron, steel)
- `army_size`: int (number of troops)
- `owned_regions`: int (territories controlled)

**Global Variables**:
- `world_peace`: bool (is there active conflict?)
- `total_casualties`: int (cumulative losses)
- `dominant_tech`: categorical (most advanced tech in use)

---

## Step 1: Create Configuration File

Create `examples/military_simulation.yaml`:

```yaml
# Military Technology Simulation
simulation:
  name: "Military Tech Race"
  max_turns: 50
  checkpoint_interval: 10

engine:
  type: economic  # Reusing existing engine for demo
  interest_rate: 0.0  # Not used in this simulation

# NEW: Define state variables
state_variables:
  agent_vars:
    tech_level:
      type: categorical
      values: [stone, bronze, iron, steel]
      default: stone
    army_size:
      type: int
      min: 0
      max: 100000
      default: 1000
    owned_regions:
      type: int
      min: 0
      max: 100
      default: 1

  global_vars:
    world_peace:
      type: bool
      default: true
    total_casualties:
      type: int
      min: 0
      default: 0
    dominant_tech:
      type: categorical
      values: [stone, bronze, iron, steel]
      default: stone

# Agents
agents:
  - name: Empire_A
    type: nation
    initial_economic_strength: 0  # Not used, but required by existing schema

  - name: Empire_B
    type: nation
    initial_economic_strength: 0

# Validation
validator:
  type: always_valid

# Logging
logging:
  level: INFO
  format: json
```

**Key Points**:
- `state_variables` section is NEW
- `agent_vars` define per-agent state
- `global_vars` define world-level state
- Each variable has: `type`, constraints (`min`/`max` or `values`), and `default`
- Variable names can be anything (no hardcoded assumptions)

---

## Step 2: Run the Simulation

```bash
# From repository root
python main.py examples/military_simulation.yaml
```

**Expected Output**:
```
{"event": "simulation_start", "name": "Military Tech Race", "turns": 50}
{"event": "turn_start", "turn": 1}
{"event": "agent_state", "agent": "Empire_A", "tech_level": "stone", "army_size": 1000, "owned_regions": 1}
{"event": "agent_state", "agent": "Empire_B", "tech_level": "stone", "army_size": 1000, "owned_regions": 1}
{"event": "global_state", "world_peace": true, "total_casualties": 0, "dominant_tech": "stone"}
...
{"event": "checkpoint_saved", "turn": 10, "file": "output/run_xyz/turn_010.json"}
...
{"event": "simulation_complete", "final_turn": 50}
```

---

## Step 3: Inspect Checkpoint

```bash
# View checkpoint file
cat output/run_xyz/turn_010.json | jq .
```

**Expected Structure**:
```json
{
  "metadata": {
    "run_id": "xyz",
    "turn": 10,
    "timestamp": "2025-10-01T10:30:00Z",
    "schema_hash": "a3f2d1e4c5b6a7f8d9e0c1b2a3f4d5e6..."
  },
  "state": {
    "turn": 10,
    "agents": {
      "Empire_A": {
        "name": "Empire_A",
        "tech_level": "bronze",
        "army_size": 1500,
        "owned_regions": 2
      },
      "Empire_B": {
        "name": "Empire_B",
        "tech_level": "stone",
        "army_size": 1200,
        "owned_regions": 1
      }
    },
    "global_state": {
      "world_peace": false,
      "total_casualties": 50,
      "dominant_tech": "bronze"
    },
    "reasoning_chains": []
  }
}
```

**Observations**:
- `metadata.schema_hash` is present (NEW)
- Agent states contain custom variables (`tech_level`, `army_size`, `owned_regions`)
- No hardcoded `economic_strength` field
- Global state contains custom variables (`world_peace`, `total_casualties`, `dominant_tech`)

---

## Step 4: Verify Constraint Enforcement

### Test 1: Invalid Type in Config

Edit config to use unsupported type:

```yaml
state_variables:
  agent_vars:
    score:
      type: complex_number  # ❌ Invalid type
      default: 0
```

Run simulation:
```bash
python main.py examples/bad_config.yaml
```

**Expected Error**:
```
ConfigValidationError: Unsupported variable type 'complex_number'
Supported types: bool, categorical, float, int
Location: state_variables.agent_vars.score.type
```

### Test 2: Constraint Violation (if engine attempts invalid update)

If the engine tries to set `army_size` to a negative value:

**Expected Error** (in logs):
```
ValidationError: Constraint violation
  Agent: Empire_A
  Variable: army_size
  Attempted value: -100
  Constraint: min=0
  Action: Update rejected
```

### Test 3: Schema Compatibility

Run simulation → create checkpoint → modify config → try to load checkpoint:

```bash
# 1. Run with original config
python main.py examples/military_simulation.yaml

# 2. Modify config (change variable definitions)
# Edit military_simulation.yaml: add new variable 'morale'

# 3. Try to resume from checkpoint
python main.py examples/military_simulation.yaml --resume output/run_xyz/turn_010.json
```

**Expected Error**:
```
SchemaCompatibilityError: Checkpoint schema mismatch
  Checkpoint schema: a3f2d1e4...
  Current schema: b8e4c2f1...
  Cause: Variable definitions have changed
  Action: Cannot load checkpoint with different variable schema
```

---

## Step 5: Compare with Legacy Config

Create an economic simulation without `state_variables` section:

```yaml
# examples/legacy_economic.yaml
simulation:
  name: "Legacy Economic Sim"
  max_turns: 10

engine:
  type: economic
  interest_rate: 0.05

agents:
  - name: Nation_A
    type: nation
    initial_economic_strength: 1000.0

validator:
  type: always_valid

# NO state_variables section (backward compatibility mode)
```

Run it:
```bash
python main.py examples/legacy_economic.yaml
```

**Expected Behavior**:
- Logs deprecation warning: "Config missing 'state_variables' section. Using legacy defaults."
- Agent states have `economic_strength` field (implicit default)
- Global state has `interest_rate`, `gdp_growth`, etc. (implicit defaults)
- Simulation runs normally

---

## Validation Checklist

After implementing this feature, verify:

- [ ] **Config Loading**
  - [x] Config with `state_variables` loads successfully
  - [x] Config without `state_variables` uses defaults + warns
  - [x] Invalid variable type rejected at load time
  - [x] Constraint violations in defaults rejected at load time

- [ ] **State Initialization**
  - [x] Agent states created with configured variables
  - [x] Global state created with configured variables
  - [x] Default values applied correctly
  - [x] No hardcoded variables present (unless using defaults)

- [ ] **Runtime Validation**
  - [x] Numeric constraints enforced (min/max)
  - [x] Categorical constraints enforced (values list)
  - [x] Type checking enforced (no bool to int, etc.)
  - [x] Validation errors have clear messages

- [ ] **Checkpoint Operations**
  - [x] Checkpoint saves include schema_hash
  - [x] Checkpoint load validates schema compatibility
  - [x] Schema mismatch rejected with clear error
  - [x] Compatible checkpoint loads successfully

- [ ] **Examples**
  - [x] Military simulation config works
  - [x] Economic simulation with custom vars works
  - [x] Legacy config (no state_variables) works with deprecation warning

---

## Common Issues & Solutions

### Issue: "Missing required field 'values' for categorical"
**Cause**: Categorical variable defined without `values` list
**Solution**: Add `values` field with at least one string value

### Issue: "Default value X violates constraint min=Y"
**Cause**: Default value outside min/max range
**Solution**: Adjust default to be within [min, max] or relax constraints

### Issue: "Reserved variable name 'name' not allowed"
**Cause**: Trying to define agent variable named "name" (reserved for agent ID)
**Solution**: Use different variable name (e.g., "display_name", "title")

### Issue: Checkpoint load fails after config change
**Cause**: Variable definitions changed (schema hash mismatch)
**Solution**: Either:
1. Revert config to original definitions, OR
2. Start new simulation (cannot resume with different schema)

---

## Next Steps

1. **Custom Engine**: Implement engine logic that uses your custom variables
   - Read from `agent_state.tech_level`, `global_state.world_peace`
   - Update values via `agent_state.model_copy(update={'army_size': new_value})`

2. **Custom Validator**: Validate state changes specific to your domain
   - E.g., "tech_level cannot decrease" or "total_casualties must be monotonic"

3. **Advanced Configs**: Explore complex variable combinations
   - Mix of numeric, boolean, and categorical variables
   - Different variables for different agent types (future enhancement)

4. **Performance Tuning**: Optimize for large-scale simulations
   - Test with 50+ variables and 100+ agents
   - Monitor checkpoint save/load times

---

## API Reference (Quick)

### Config YAML Structure
```yaml
state_variables:
  agent_vars:
    <variable_name>:
      type: float | int | bool | categorical
      min: <number>           # Optional: for float/int
      max: <number>           # Optional: for float/int
      values: [<strings>]     # Required: for categorical
      default: <value>        # Required: initial value

  global_vars:
    # Same structure as agent_vars
```

### Accessing Variables in Code
```python
# Reading
tech = agent_state.tech_level
peace = global_state.world_peace

# Updating (creates new immutable instance)
new_agent_state = agent_state.model_copy(update={'army_size': 2000})
new_global_state = global_state.model_copy(update={'total_casualties': 100})

# Validation happens automatically - raises ValidationError if constraints violated
```

### Schema Hash Computation (internal)
```python
from llm_sim.models.state import compute_schema_hash

hash_value = compute_schema_hash(agent_vars, global_vars)
# Returns: "a3f2d1e4c5b6a7f8..." (64-char SHA-256 hex)
```

---

## Testing Your Implementation

```bash
# Run unit tests
pytest tests/unit/test_variable_definitions.py
pytest tests/unit/test_dynamic_models.py

# Run contract tests
pytest tests/contract/test_config_schema.py
pytest tests/contract/test_checkpoint_schema.py

# Run integration tests
pytest tests/integration/test_custom_variables.py

# Run this quickstart as acceptance test
pytest tests/acceptance/test_quickstart_military_sim.py
```

---

## Success Criteria

This feature is complete when:

1. ✅ All 7 acceptance scenarios from spec pass
2. ✅ Config and checkpoint schemas validate correctly
3. ✅ Backward compatibility maintained (legacy configs work)
4. ✅ Military simulation example runs end-to-end
5. ✅ Schema compatibility enforced (mismatched checkpoint rejected)
6. ✅ Error messages are clear and actionable
7. ✅ Documentation complete (this quickstart + data-model.md)

---

*Quickstart complete - ready for implementation*
