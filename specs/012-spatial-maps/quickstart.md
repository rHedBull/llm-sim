# Quickstart: Grid-Based Epidemic Simulation

**Feature**: 012-spatial-maps
**Purpose**: Validate spatial features through end-to-end scenario
**Duration**: ~5 minutes

## Scenario Overview

Simulate disease spread on a 10×10 grid where:
- Agents (people) are positioned at random grid cells
- Infection spreads to agents in adjacent cells (4-connectivity)
- Infected agents move randomly to spread disease
- Validators ensure agents only move to adjacent cells
- Spatial state persists to checkpoints

## Prerequisites

```bash
# Install dependencies
uv add networkx

# Ensure tests pass
uv run pytest tests/contract/test_spatial_*.py
```

## Step 1: Create Configuration

**File**: `examples/epidemic_grid_config.yaml`

```yaml
simulation:
  name: "Grid Epidemic"
  max_turns: 20
  checkpoint_interval: 5

# Spatial topology: 10×10 grid
spatial:
  topology:
    type: "grid"
    width: 10
    height: 10
    connectivity: 4
    wrapping: false

  # Initial location attributes
  location_attributes:
    "5,5":
      infection_source: true

engine:
  type: "epidemic_engine"

agents:
  - name: "person_0"
    type: "random_walker"
    initial_location: "5,5"  # Start at center (infected)
  - name: "person_1"
    type: "random_walker"
    initial_location: "4,5"
  - name: "person_2"
    type: "random_walker"
    initial_location: "6,5"
  - name: "person_3"
    type: "random_walker"
    initial_location: "5,4"
  - name: "person_4"
    type: "random_walker"
    initial_location: "5,6"

validator:
  type: "spatial_movement_validator"

state_variables:
  agent_vars:
    infected:
      type: bool
      default: false
  global_vars:
    total_infected:
      type: int
      default: 1
```

## Step 2: Verify Spatial State Initialization

**Test**: Spatial state created correctly from config

```python
from llm_sim.models.config import load_config
from llm_sim.infrastructure.spatial.factory import SpatialStateFactory

# Load config
config = load_config("examples/epidemic_grid_config.yaml")

# Create spatial state
spatial_state = SpatialStateFactory.create(config.spatial)

# Verify topology
assert spatial_state.topology_type == "grid"
assert len(spatial_state.locations) == 100  # 10×10 grid

# Verify "default" network exists
assert "default" in spatial_state.networks

# Verify location (5,5) has attribute
assert spatial_state.locations["5,5"].attributes.get("infection_source") == True

# Verify agents not yet positioned (happens in orchestrator)
assert len(spatial_state.agent_positions) == 0
```

**Expected**: All assertions pass, grid created with 100 locations

## Step 3: Test Agent Spatial Queries

**Test**: Agents can query their position and neighbors

```python
from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.infrastructure.spatial.mutations import SpatialMutations

# Place agent at (5,5)
spatial_state = SpatialMutations.move_agent(spatial_state, "person_0", "5,5")

# Query position
position = SpatialQuery.get_agent_position(spatial_state, "person_0")
assert position == "5,5"

# Query neighbors (4-connectivity)
neighbors = SpatialQuery.get_neighbors(spatial_state, "5,5", network="default")
assert set(neighbors) == {"4,5", "6,5", "5,4", "5,6"}

# Query agents at location
agents_here = SpatialQuery.get_agents_at(spatial_state, "5,5")
assert "person_0" in agents_here
```

**Expected**: Agent queries work correctly, neighbors identified

## Step 4: Test Movement Validation

**Test**: Validator rejects invalid moves

```python
from llm_sim.models.action import Action

# Valid move: (5,5) → (5,6) is adjacent
action_valid = Action(
    agent_name="person_0",
    type="move",
    parameters={"target_location": "5,6"}
)

# Invalid move: (5,5) → (8,8) is not adjacent
action_invalid = Action(
    agent_name="person_0",
    type="move",
    parameters={"target_location": "8,8"}
)

# Validator should allow valid, reject invalid
from llm_sim.infrastructure.validators.spatial_movement_validator import SpatialMovementValidator

validator = SpatialMovementValidator()
result_valid = validator.validate_action(action_valid, state)
assert result_valid.valid == True

result_invalid = validator.validate_action(action_invalid, state)
assert result_invalid.valid == False
assert "not adjacent" in result_invalid.reason.lower()
```

**Expected**: Adjacent moves allowed, non-adjacent moves rejected

## Step 5: Test Infection Spread

**Test**: Engine spreads infection to adjacent agents

```python
# Initial state: person_0 infected at (5,5)
# person_1 at (4,5) - adjacent, should get infected

# Engine checks adjacent cells for infection spread
current_pos = SpatialQuery.get_agent_position(spatial_state, "person_0")
nearby_agents = SpatialQuery.get_agents_within(spatial_state, current_pos, radius=1)

# Apply infection logic
for agent_name in nearby_agents:
    if agent_name != "person_0":
        # Mark as infected (engine updates agent state)
        # ... engine logic ...
        pass

# Verify person_1 now infected
# (This would be verified through agent state, not spatial state)
```

**Expected**: Engine can identify nearby agents for infection logic

## Step 6: Test Checkpoint Persistence

**Test**: Spatial state persists and restores correctly

```python
from llm_sim.persistence.checkpoint_manager import CheckpointManager
from llm_sim.models.state import SimulationState

# Create state with spatial_state
state = SimulationState(
    turn=5,
    agents={},  # populated agents
    global_state=global_state,
    spatial_state=spatial_state
)

# Save checkpoint
checkpoint_manager = CheckpointManager(
    run_id="test_epidemic",
    agent_var_defs=agent_vars,
    global_var_defs=global_vars
)
checkpoint_manager.save_checkpoint(state)

# Load checkpoint
restored_state = checkpoint_manager.load_checkpoint("test_epidemic", turn=5)

# Verify spatial state restored
assert restored_state.spatial_state is not None
assert restored_state.spatial_state.topology_type == "grid"
assert len(restored_state.spatial_state.locations) == 100
assert restored_state.spatial_state.agent_positions == spatial_state.agent_positions
```

**Expected**: Spatial state serializes to JSON and deserializes correctly

## Step 7: Run Full Simulation

**Test**: Complete simulation with spatial features

```bash
# Run simulation
uv run python -m llm_sim.main examples/epidemic_grid_config.yaml

# Verify output
ls output/grid_epidemic_*

# Check checkpoints have spatial state
uv run python -c "
import json
with open('output/grid_epidemic_*/turn_5_checkpoint.json') as f:
    data = json.load(f)
    assert 'spatial_state' in data
    assert data['spatial_state']['topology_type'] == 'grid'
    print('✓ Spatial state in checkpoint')
"
```

**Expected**: Simulation runs, checkpoints contain spatial_state

## Step 8: Verify Backward Compatibility

**Test**: Existing simulations without spatial config still work

```yaml
# config_no_spatial.yaml
simulation:
  name: "No Spatial"
  max_turns: 5

engine:
  type: "economic"

agents:
  - name: "agent_1"
    type: "llm_agent"

validator:
  type: "always_valid"

# NO spatial field
```

```bash
# Run simulation without spatial config
uv run python -m llm_sim.main examples/config_no_spatial.yaml

# Verify runs successfully
# Verify state.spatial_state is None
```

**Expected**: Non-spatial simulations unaffected

## Success Criteria

All steps complete with:
- ✅ Spatial state created from grid config
- ✅ Agents query positions and neighbors
- ✅ Validator enforces adjacency constraints
- ✅ Engine uses spatial queries for logic
- ✅ Checkpoints persist spatial state
- ✅ Backward compatibility maintained

## Next Steps

After quickstart passes:
1. Implement remaining topology types (hex, network, geojson)
2. Add proximity-based observability filtering
3. Create additional example simulations
4. Performance test with 1000+ locations
