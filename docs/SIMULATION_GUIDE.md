# Simulation Creation Guide

**A comprehensive guide to creating and configuring simulations with the llm-sim framework.**

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [State Variables](#state-variables)
4. [Spatial Positioning](#spatial-positioning)
5. [Partial Observability](#partial-observability)
6. [Dynamic Agent Management](#dynamic-agent-management)
7. [Agent Configuration](#agent-configuration)
8. [Engine Configuration](#engine-configuration)
9. [Validator Configuration](#validator-configuration)
10. [LLM Integration](#llm-integration)
11. [Checkpointing](#checkpointing)
12. [Complete Examples](#complete-examples)

---

## Overview

Simulations in llm-sim are configured using YAML files that define:

- **State variables** - What data agents track
- **Agents** - Who makes decisions
- **Engine** - How the world evolves
- **Validator** - What actions are valid
- **Observability** - What information agents can see
- **Spatial positioning** - Where agents are located (optional)
- **LLM settings** - How agents reason
- **Simulation parameters** - Runtime configuration

---

## Configuration Structure

A complete configuration file has this structure:

```yaml
simulation:
  name: "My Simulation"
  max_turns: 100
  checkpoint_interval: 10

state_variables:
  agent_vars:
    # Agent-specific variables
  global_vars:
    # Shared global state

agents:
  - name: Agent1
    type: my_agent
    initial_location: "0,0"  # Optional: spatial positioning

engine:
  type: my_engine

validator:
  type: my_validator

spatial:  # Optional: spatial topology
  topology:
    type: grid
    width: 10
    height: 10

observability:
  enabled: true
  # Partial observability configuration

llm:
  model: "llama3.2"
  host: "http://localhost:11434"

logging:
  level: "INFO"
  format: "json"
```

---

## State Variables

Define custom state variables that agents track. The framework generates Pydantic models from these definitions.

### Agent Variables

Variables that each agent tracks individually:

```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 100.0
      description: "Agent's economic power"

    tech_level:
      type: int
      min: 1
      max: 10
      default: 1
      description: "Technology advancement level"

    alliance:
      type: str
      default: "neutral"
      description: "Current alliance membership"

    is_active:
      type: bool
      default: true
      description: "Whether agent is participating"
```

### Global Variables

Variables shared across all agents:

```yaml
state_variables:
  global_vars:
    interest_rate:
      type: float
      min: 0.0
      max: 1.0
      default: 0.05
      description: "Global interest rate"

    turn:
      type: int
      default: 0
      description: "Current simulation turn"

    total_wealth:
      type: float
      default: 0.0
      description: "Sum of all agent wealth"
```

### Variable Types

Supported types:

| Type | Example | Constraints |
|------|---------|-------------|
| `float` | `economic_strength: 100.0` | `min`, `max` |
| `int` | `tech_level: 5` | `min`, `max` |
| `str` | `alliance: "NATO"` | - |
| `bool` | `is_active: true` | - |

### Variable Constraints

Optional validation constraints:

```yaml
economic_strength:
  type: float
  min: 0          # Minimum value (inclusive)
  max: 1000       # Maximum value (inclusive)
  default: 100.0  # Initial value
```

---

## Spatial Positioning

Add spatial topology to your simulation, enabling agents to exist at locations, move through space, and interact based on proximity.

### Overview

Spatial positioning enables:
- **Location-based agents** - Agents positioned at specific locations
- **Spatial topologies** - Grid, hex, network, or geographic regions
- **Movement constraints** - Validate actions based on adjacency
- **Proximity awareness** - Filter observations by distance
- **Multi-layer networks** - Multiple connectivity patterns (roads, trade routes, etc.)

### Basic Setup

```yaml
spatial:
  topology:
    type: grid        # or hex_grid, network, geojson
    width: 10
    height: 10
    connectivity: 4   # 4-way or 8-way
    wrapping: false   # toroidal grid

agents:
  - name: Agent1
    type: my_agent
    initial_location: "5,5"  # Place agent at grid cell (5,5)
```

### Topology Types

#### Grid Topology

Regular 2D rectangular grid:

```yaml
spatial:
  topology:
    type: grid
    width: 10         # Grid width
    height: 10        # Grid height
    connectivity: 4   # 4 or 8 (diagonal neighbors)
    wrapping: false   # true for toroidal (edges wrap)
```

**Location IDs**: `"x,y"` format (e.g., `"0,0"`, `"5,3"`)

**Use cases**: City grids, cellular automata, epidemic spread

#### Hexagonal Grid Topology

Hexagonal grid with 6-neighbor connectivity:

```yaml
spatial:
  topology:
    type: hex_grid
    radius: 5         # Hexagonal radius from center
    coord_system: axial
```

**Location IDs**: `"q,r"` format in axial coordinates (e.g., `"0,0"`, `"-1,2"`)

**Use cases**: Board games, territorial maps, resource distribution

#### Network Topology

Arbitrary graph from JSON file:

```yaml
spatial:
  topology:
    type: network
    edges_file: "path/to/network.json"
```

**JSON Format**:
```json
{
  "nodes": ["nodeA", "nodeB", "nodeC"],
  "edges": [
    ["nodeA", "nodeB"],
    ["nodeB", "nodeC"]
  ],
  "attributes": {
    "nodeA": {"capacity": 100}
  }
}
```

**Location IDs**: Node names from JSON

**Use cases**: Supply chains, social networks, transportation networks

#### GeoJSON Topology

Geographic regions from GeoJSON polygons:

```yaml
spatial:
  topology:
    type: geojson
    geojson_file: "path/to/regions.geojson"
```

**GeoJSON Format**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Region1",
        "population": 100000,
        "resources": 500
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]
      }
    }
  ]
}
```

**Location IDs**: Region names from `properties.name`

**Use cases**: Geopolitics, regional economics, territorial control

### Location Attributes

Add attributes to specific locations:

```yaml
spatial:
  topology:
    type: grid
    width: 10
    height: 10

  location_attributes:
    "5,5":
      terrain: "mountain"
      resources: 100
      danger_level: 0.8
    "3,7":
      terrain: "water"
      passable: false
```

**Access in code**:
```python
from llm_sim.infrastructure.spatial.query import SpatialQuery

terrain = SpatialQuery.get_location_attribute(state.spatial_state, "5,5", "terrain")
# Returns: "mountain"
```

### Multi-Layer Networks

Add overlay networks beyond base topology:

```yaml
spatial:
  topology:
    type: grid
    width: 10
    height: 10

  additional_networks:
    - name: "trade_routes"
      edges_file: "data/trade.json"
    - name: "alliances"
      edges_file: "data/alliances.json"
```

**Use cases**:
- Transportation modes (road, rail, air)
- Social connections (friends, allies, enemies)
- Communication networks
- Trade relationships

### Agent Positioning

Place agents at initial locations:

```yaml
agents:
  - name: Agent1
    type: my_agent
    initial_location: "5,5"

  - name: Agent2
    type: my_agent
    initial_location: "winterfell"  # For GeoJSON/network topologies

  - name: Agent3
    type: my_agent
    # No initial_location = agent not spatially positioned
```

**Moving agents** (in engines):
```python
from llm_sim.infrastructure.spatial.mutations import SpatialMutations

new_spatial_state = SpatialMutations.move_agent(
    state.spatial_state,
    agent_name="Agent1",
    new_location="6,5"
)
```

### Proximity-Based Observations

Automatically filter observations by proximity:

```yaml
spatial:
  topology:
    type: grid
    width: 20
    height: 20
  proximity_radius: 3  # Agents only see within 3 hops
```

Agents automatically receive filtered observations containing only:
- Agents within `proximity_radius` hops
- Locations within `proximity_radius` hops
- Global state (unchanged)

**Composability**: Works with partial observability:
1. Spatial filtering applies first (proximity)
2. Observability filtering applies second (visibility rules)

### Spatial Queries

Query spatial relationships in agent/engine/validator code:

```python
from llm_sim.infrastructure.spatial.query import SpatialQuery

# Get agent position
location = SpatialQuery.get_agent_position(state.spatial_state, "Agent1")

# Get neighboring locations
neighbors = SpatialQuery.get_neighbors(state.spatial_state, "5,5")

# Check adjacency
adjacent = SpatialQuery.is_adjacent(state.spatial_state, "5,5", "5,6")

# Find shortest path
path = SpatialQuery.shortest_path(state.spatial_state, "5,5", "8,8")

# Get agents at location
agents_here = SpatialQuery.get_agents_at(state.spatial_state, "5,5")

# Get nearby agents
nearby = SpatialQuery.get_agents_within(state.spatial_state, "5,5", radius=2)

# Get location attributes
terrain = SpatialQuery.get_location_attribute(state.spatial_state, "5,5", "terrain")
```

### Spatial Mutations

Modify spatial state (engines only):

```python
from llm_sim.infrastructure.spatial.mutations import SpatialMutations

# Move single agent
new_state = SpatialMutations.move_agent(spatial_state, "Agent1", "6,5")

# Move multiple agents
moves = {"Agent1": "6,5", "Agent2": "7,3"}
new_state = SpatialMutations.move_agents_batch(spatial_state, moves)

# Update location attributes
new_state = SpatialMutations.set_location_attribute(
    spatial_state, "5,5", "resources", 150
)

# Add network connection
new_state = SpatialMutations.add_connection(
    spatial_state,
    loc1="cityA",
    loc2="cityB",
    network="trade_routes",
    attributes={"cost": 100, "time": 5}
)
```

**All mutations are immutable** - return new spatial state, never mutate input.

### Movement Validation

Validate spatial actions in validators:

```python
from llm_sim.infrastructure.base import BaseValidator
from llm_sim.infrastructure.spatial.query import SpatialQuery

class SpatialMovementValidator(BaseValidator):
    def validate_action(self, action, state):
        if action.action_name == "move":
            current_loc = SpatialQuery.get_agent_position(
                state.spatial_state,
                action.agent_name
            )
            target_loc = action.parameters["target"]

            # Check adjacency
            if not SpatialQuery.is_adjacent(
                state.spatial_state,
                current_loc,
                target_loc
            ):
                return ValidationResult(
                    valid=False,
                    reason=f"Location {target_loc} not adjacent to {current_loc}"
                )

        return ValidationResult(valid=True)
```

### Complete Spatial Example

```yaml
simulation:
  name: "Grid Epidemic"
  max_turns: 50

spatial:
  topology:
    type: grid
    width: 10
    height: 10
    connectivity: 4
    wrapping: false

  location_attributes:
    "5,5":
      infection_source: true

agents:
  - name: person_0
    type: random_walker
    initial_location: "5,5"  # Initial infected

  - name: person_1
    type: random_walker
    initial_location: "4,5"

  - name: person_2
    type: random_walker
    initial_location: "6,5"

engine:
  type: epidemic_engine

validator:
  type: spatial_movement_validator

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

### Backward Compatibility

Spatial features are completely optional:

```yaml
# Simulations without spatial config work unchanged
agents:
  - name: Agent1
    type: my_agent
    # No initial_location needed

# No spatial config section required
```

When `spatial` is omitted:
- `state.spatial_state` is `None`
- Spatial queries return safe defaults
- Proximity filtering is skipped
- All existing functionality works unchanged

### Use Cases

**Grid-Based**:
- Epidemic simulations (disease spread through grid cells)
- Cellular automata (Conway's Life, forest fires)
- Urban planning (city development on grid)
- Tactical games (turn-based combat)

**Network-Based**:
- Supply chain optimization
- Social network dynamics
- Transportation routing
- Communication networks

**Geographic**:
- Geopolitical simulations
- Resource competition
- Territorial control
- Trade route optimization

### Performance Considerations

- Spatial queries are highly optimized (most < 1ms)
- Shortest path uses NetworkX (< 10ms for 1000 locations)
- Proximity filtering is O(agents + locations)
- Immutable updates use Pydantic model_copy (efficient)

### Example Files

See `examples/spatial/` for complete working examples:
- `epidemic_grid_config.yaml` - Grid epidemic simulation
- `geopolitics_config.yaml` - GeoJSON geopolitical game
- `supply_chain_config.yaml` - Network supply chain

---

## Partial Observability

Control what information each agent can see. This enables realistic simulations where agents have incomplete or noisy information.

### Basic Setup

```yaml
observability:
  enabled: true

  variable_visibility:
    external: [economic_strength, position]
    internal: [secret_reserves, strategy]

  matrix:
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, Agent3, unaware, null]
    - [Agent1, global, external, 0.1]

  default:
    level: external
    noise: 0.1
```

### Observability Levels

Three levels control what agents can see:

| Level | Meaning | Use Case |
|-------|---------|----------|
| `unaware` | Target is completely invisible | Unknown agents, hidden actors |
| `external` | Only public variables visible | Competitors, public information |
| `insider` | All variables visible | Allies, own state, trusted sources |

### Variable Visibility

Classify variables as external (public) or internal (private):

```yaml
variable_visibility:
  external:
    - economic_strength  # Public information
    - position
    - tech_level

  internal:
    - secret_reserves    # Private information
    - hidden_strategy
    - internal_plans
```

**Rules:**
- Variables in `external` list are visible to `external` and `insider` observers
- Variables in `internal` list are only visible to `insider` observers
- Variables not listed default to `external` (backward compatible)
- No variable can be in both lists (validation error)

### Observability Matrix

Define observer-target relationships:

```yaml
matrix:
  # Format: [observer, target, level, noise]

  # Agent observes self perfectly
  - [Agent1, Agent1, insider, 0.0]

  # Agent observes competitor with noise
  - [Agent1, Agent2, external, 0.2]

  # Agent unaware of hidden actor
  - [Agent1, Agent3, unaware, null]

  # Agent observes global state
  - [Agent1, global, external, 0.1]
```

**Matrix Entry Format:**
- `observer`: Agent ID making the observation
- `target`: Agent ID or "global" being observed
- `level`: `unaware`, `external`, or `insider`
- `noise`: Float ≥ 0.0 (noise factor) or `null` for unaware

### Noise Model

Deterministic multiplicative noise is applied to numeric variables:

```yaml
# 0.2 noise means ±20% variation
- [Agent1, Agent2, external, 0.2]
```

**Noise Properties:**
- **Deterministic**: Same seed → same noise value (reproducible)
- **Multiplicative**: `noisy_value = true_value * (1.0 + random[-noise, +noise])`
- **Bounded**: Noise factor controls max deviation
- **Seeded**: Based on `(turn, observer_id, variable_name)`

**Example:**
```python
# True value: economic_strength = 1000.0
# Noise factor: 0.2 (±20%)
# Possible noisy value: 850.0 (15% below)
# Range: [800.0, 1200.0]
```

**Special Cases:**
- `noise: 0.0` - No noise, perfect information
- `noise: null` - For unaware level (not used)
- Integer values are noised then rounded

### Default Observability

Fallback for undefined observer-target pairs:

```yaml
default:
  level: external      # Default observability level
  noise: 0.1          # Default noise factor
```

**When used:**
- Observer-target pair not in matrix
- Allows sparse matrix configuration
- Common pattern: default to limited visibility

### Asymmetric Visibility

Agents can have different views of each other:

```yaml
matrix:
  # Agent1 sees Agent2
  - [Agent1, Agent2, external, 0.2]

  # Agent2 cannot see Agent1 (not in matrix)
  # Falls back to default (or unaware if default.level = unaware)
```

### Global State Observability

Global state is treated like any agent:

```yaml
matrix:
  # Full access to global state
  - [Agent1, global, insider, 0.0]

  # Limited access with noise
  - [Agent2, global, external, 0.15]

  # No access to global state
  - [Agent3, global, unaware, null]
```

### Backward Compatibility

Full observability (legacy behavior):

```yaml
# Option 1: Disable observability
observability:
  enabled: false

# Option 2: Omit observability section entirely
# (observability is optional)
```

When disabled or omitted, agents receive complete ground truth state.

### Complete Observability Example

```yaml
observability:
  enabled: true

  # Classify variables
  variable_visibility:
    external:
      - economic_strength
      - position
      - public_policy
    internal:
      - secret_reserves
      - hidden_strategy
      - intelligence_budget

  # Define observer-target relationships
  matrix:
    # Agent1 (insider to self, external to others)
    - [Agent1, Agent1, insider, 0.0]
    - [Agent1, Agent2, external, 0.2]
    - [Agent1, Agent3, external, 0.2]
    - [Agent1, global, external, 0.1]

    # Agent2 (similar setup)
    - [Agent2, Agent2, insider, 0.0]
    - [Agent2, Agent1, external, 0.15]
    - [Agent2, Agent3, unaware, null]  # Doesn't know Agent3 exists
    - [Agent2, global, external, 0.1]

    # Agent3 (spy with insider access to Agent1)
    - [Agent3, Agent3, insider, 0.0]
    - [Agent3, Agent1, insider, 0.05]  # Infiltrated Agent1
    - [Agent3, Agent2, external, 0.2]
    - [Agent3, global, insider, 0.0]   # Full global knowledge

  # Default for undefined pairs
  default:
    level: unaware  # Hidden by default
    noise: 0.0
```

### Observability Use Cases

**1. Economic Competition**
```yaml
# Companies see competitors' public data with noise
- [CompanyA, CompanyB, external, 0.15]
```

**2. Intelligence Networks**
```yaml
# Spy has insider access to target
- [Spy, Target, insider, 0.05]
```

**3. Fog of War**
```yaml
# Military units aware of nearby units, unaware of distant ones
- [Unit1, Unit2, external, 0.3]  # Nearby
- [Unit1, Unit3, unaware, null]  # Distant
```

**4. Information Asymmetry**
```yaml
# Central bank has perfect global view
- [CentralBank, global, insider, 0.0]
# Commercial banks have noisy view
- [Bank1, global, external, 0.1]
```

**5. Trust Networks**
```yaml
# Allied agents share insider information
- [Ally1, Ally2, insider, 0.0]
# Neutral agents see public data
- [Neutral1, Ally1, external, 0.2]
```

---

## Dynamic Agent Management

Control the agent population dynamically during simulation runtime. Agents can be added, removed, or temporarily paused without restarting the simulation.

### Overview

Dynamic agent management enables:
- **Runtime population changes** - Add/remove agents at any turn
- **Agent-initiated actions** - Agents can spawn, remove themselves, or pause
- **External control** - Orchestrator can manage agents programmatically
- **State preservation** - Paused agents retain their state for later resumption

### Core Operations

#### Adding Agents

Add new agents during simulation with initial state:

```python
from llm_sim.orchestrator import SimulationOrchestrator

orchestrator = SimulationOrchestrator.from_yaml("config.yaml")

# Add agent with initial state
orchestrator.add_agent(
    agent_name="NewTrader",
    initial_state={"wealth": 500.0, "risk_tolerance": 0.7}
)
```

**Features:**
- Agents begin participating in the next turn
- Automatic name collision resolution (appends numeric suffix)
- Validates against maximum agent limit (default: 25)

**Name Collision Example:**
```python
orchestrator.add_agent("Trader")  # Creates "Trader"
orchestrator.add_agent("Trader")  # Auto-renamed to "Trader_1"
orchestrator.add_agent("Trader")  # Auto-renamed to "Trader_2"
```

#### Removing Agents

Permanently remove agents from the simulation:

```python
orchestrator.remove_agent("OldTrader")
```

**Effects:**
- Agent no longer participates in any future turns
- Agent data excluded from active agent queries
- If paused, also removed from pause tracking
- State snapshots no longer include the removed agent

#### Pausing Agents

Temporarily deactivate agents while preserving their state:

```python
# Pause indefinitely
orchestrator.pause_agent("Trader1")

# Pause with auto-resume after N turns
orchestrator.pause_agent("Trader1", auto_resume_turns=5)
```

**Pause Behavior:**
- Agent skips all decision-making during pause
- Complete state preserved while paused
- Can be manually resumed or auto-resumed
- Multiple agents can be paused simultaneously

#### Resuming Agents

Reactivate a paused agent:

```python
orchestrator.resume_agent("Trader1")
```

**Resume Behavior:**
- Agent resumes participation from preserved state
- Begins participating in the next turn
- Auto-resume countdown canceled (if configured)

### Agent-Initiated Lifecycle Changes

Agents can request lifecycle changes through special lifecycle actions. These are separated from regular actions and processed after all turn actions complete.

#### Agent Self-Removal

Agents can request their own removal:

```python
# In your agent's decide_action method
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation

def decide_action(self, state: SimulationState) -> Action:
    if self.should_exit():
        return LifecycleAction(
            operation=LifecycleOperation.REMOVE_AGENT,
            initiating_agent=self.name,
            target_agent_name=self.name
        )
```

#### Agent Spawning

Agents can spawn new agents:

```python
def decide_action(self, state: SimulationState) -> Action:
    if self.should_spawn_child():
        return LifecycleAction(
            operation=LifecycleOperation.ADD_AGENT,
            initiating_agent=self.name,
            target_agent_name="ChildAgent",
            initial_state={"wealth": 100.0}
        )
```

#### Agent Self-Pause

Agents can request temporary pause:

```python
def decide_action(self, state: SimulationState) -> Action:
    if self.should_hibernate():
        return LifecycleAction(
            operation=LifecycleOperation.PAUSE_AGENT,
            initiating_agent=self.name,
            target_agent_name=self.name,
            auto_resume_turns=10  # Wake up after 10 turns
        )
```

### Validation and Constraints

All lifecycle operations undergo validation:

**Maximum Agent Limit:**
```python
# Default: 25 agents maximum
# Add operations fail if limit reached
# Logged as warning, turn continues
```

**Basic Validation Checks:**
- Agent exists (for remove/pause/resume)
- Agent not already paused (for pause)
- Agent is paused (for resume)
- Count below maximum (for add)

**Validation Failure Handling:**
- Logged as warning
- Operation skipped
- Turn execution continues
- No simulation halt

### Turn Execution Flow

Lifecycle changes follow a specific execution order:

1. **Auto-Resume Processing** - Check and resume agents with elapsed auto-resume timers
2. **Agent Decision Phase** - Active agents decide actions (including lifecycle actions)
3. **Action Validation** - Regular actions validated
4. **Regular Actions** - Validated actions executed by engine
5. **Lifecycle Actions** - Lifecycle changes applied atomically
6. **State Update** - Simulation state reflects all changes

**Key Points:**
- Only active (non-paused) agents participate in decisions
- Lifecycle changes applied after all regular actions
- Multiple lifecycle changes in one turn processed together
- State updated atomically at turn end

### Configuration

No YAML configuration required - lifecycle management is built-in and always available.

Optional configuration for custom limits:

```python
# In your engine or orchestrator setup
lifecycle_manager = LifecycleManager(
    max_agents=50  # Override default limit of 25
)
```

### Auto-Resume Mechanism

Paused agents can automatically resume after a specified number of turns:

```python
# External pause with auto-resume
orchestrator.pause_agent("Agent1", auto_resume_turns=5)

# Agent self-pause with auto-resume
LifecycleAction(
    operation=LifecycleOperation.PAUSE_AGENT,
    target_agent_name=self.name,
    auto_resume_turns=3
)
```

**Auto-Resume Process:**
- Counter decrements each turn
- Agent automatically resumes when counter reaches 0
- Manual resume cancels auto-resume countdown
- Removing paused agent cancels auto-resume

### Use Cases

**1. Birth/Death Simulations**
```python
# Agent dies when resources depleted
if self.wealth <= 0:
    return LifecycleAction(
        operation=LifecycleOperation.REMOVE_AGENT,
        target_agent_name=self.name
    )
```

**2. Dynamic Team Formation**
```python
# Spawn team member when successful
if self.milestone_reached():
    return LifecycleAction(
        operation=LifecycleOperation.ADD_AGENT,
        target_agent_name=f"{self.name}_Partner",
        initial_state={"team_leader": self.name}
    )
```

**3. Seasonal Activity**
```python
# Hibernate during off-season
if self.is_winter():
    return LifecycleAction(
        operation=LifecycleOperation.PAUSE_AGENT,
        target_agent_name=self.name,
        auto_resume_turns=10  # Resume in spring
    )
```

**4. A/B Testing**
```python
# Temporarily exclude agent for testing
orchestrator.pause_agent("TestAgent")
# Run simulation for N turns
# ...
orchestrator.resume_agent("TestAgent")
```

**5. Migration Patterns**
```python
# Agent migrates to different simulation
orchestrator.remove_agent("MigratingAgent")
# Transfer to different simulation instance
other_sim.add_agent("MigratingAgent", initial_state=saved_state)
```

### Edge Cases

**Last Agent Removal:**
- Allowed - simulation can have 0 agents
- No special handling required

**Duplicate Pause Request:**
- Validation fails (already paused)
- Logged as warning
- Original pause state preserved

**Resume Non-Paused Agent:**
- Validation fails (not paused)
- Logged as warning
- No state change

**Maximum Limit Reached:**
- Add operations fail validation
- Logged as warning
- Agent not added

**Agent References After Removal:**
- Removed agents excluded from state
- Other agents should handle missing references
- No automatic cleanup of cross-references

### Complete Example

```python
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation

# Initialize simulation
orchestrator = SimulationOrchestrator.from_yaml("config.yaml")

# External control - add agent at runtime
orchestrator.add_agent(
    agent_name="NewTrader",
    initial_state={"wealth": 1000.0}
)

# External control - pause for maintenance
orchestrator.pause_agent("MaintenanceAgent", auto_resume_turns=5)

# Run simulation
# Agents can internally request lifecycle changes:
#
# class MyAgent(BaseAgent):
#     def decide_action(self, state):
#         if self.should_spawn():
#             return LifecycleAction(
#                 operation=LifecycleOperation.ADD_AGENT,
#                 initiating_agent=self.name,
#                 target_agent_name="Offspring",
#                 initial_state={"parent": self.name}
#             )

result = orchestrator.run()

# External control - remove agent after simulation
orchestrator.remove_agent("TemporaryAgent")
```

### Best Practices

**1. Validate State After Removals**
```python
# Check if referenced agent still exists
if target_agent in state.agents:
    # Interact with agent
```

**2. Use Auto-Resume for Temporary States**
```python
# Don't: Manual resume requires tracking
orchestrator.pause_agent("Agent1")
# ... track when to resume

# Do: Let system auto-resume
orchestrator.pause_agent("Agent1", auto_resume_turns=5)
```

**3. Handle Name Collisions Gracefully**
```python
# System auto-renames, but you might want to track
actual_name = orchestrator.add_agent("Trader", initial_state)
# actual_name might be "Trader_1" if "Trader" exists
```

**4. Set Appropriate Limits**
```python
# Consider your simulation scale
lifecycle_manager = LifecycleManager(max_agents=100)
```

**5. Log Lifecycle Events**
```python
# Enable structured logging to track lifecycle changes
logging:
  level: "INFO"  # Or "DEBUG" for detailed lifecycle logs
```

---

## Agent Configuration

Define agents that make decisions:

```yaml
agents:
  - name: Agent1
    type: my_agent
    config:
      # Agent-specific parameters
      risk_tolerance: 0.7
      strategy: "aggressive"

  - name: Agent2
    type: my_agent
    config:
      risk_tolerance: 0.3
      strategy: "defensive"
```

### LLM Agents

For agents using LLM reasoning:

```yaml
agents:
  - name: Agent1
    type: llm_agent
    config:
      system_prompt: |
        You are a strategic decision maker.
        Maximize economic strength while maintaining stability.

      temperature: 0.7
      max_tokens: 500
```

---

## Engine Configuration

Define how the simulation world evolves:

```yaml
engine:
  type: economic_engine
  config:
    interest_rate: 0.05
    inflation_rate: 0.02
    growth_rate: 0.03
```

Common engine types:
- `economic_engine` - Economic simulations
- `game_engine` - Game-theoretic scenarios
- `custom_engine` - Your custom implementation

---

## Validator Configuration

Define action validation rules:

```yaml
validator:
  type: llm_validator
  config:
    domain: "economic"
    permissive: false
    max_retries: 3
```

**Permissive mode:**
- `true` - Allow invalid actions (log warnings)
- `false` - Reject invalid actions (strict validation)

---

## LLM Integration

Configure LLM settings for reasoning agents:

```yaml
llm:
  model: "llama3.2"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 3
  temperature: 0.7
  stream: true
```

### Supported LLM Providers

**Ollama (default):**
```yaml
llm:
  model: "llama3.2"
  host: "http://localhost:11434"
```

**OpenAI-compatible:**
```yaml
llm:
  model: "gpt-4"
  host: "https://api.openai.com/v1"
  api_key: "${OPENAI_API_KEY}"
```

### Model Selection

| Model | Use Case | Performance |
|-------|----------|-------------|
| `llama3.2` | Fast reasoning, local | Good for testing |
| `llama3.3:70b` | High quality reasoning | Slower, better decisions |
| `gpt-4` | Production quality | Best reasoning, requires API |
| `claude-3-opus` | Long context, nuanced | Expensive, high quality |

---

## Checkpointing

Configure state persistence:

```yaml
simulation:
  checkpoint_interval: 10  # Save every 10 turns
```

### Output Structure

```
output/{run_id}/
├── checkpoints/
│   ├── turn_10.json
│   ├── turn_20.json
│   ├── last.json    # Latest state
│   └── final.json   # Final state
├── logs/
│   └── simulation.log
└── result.json      # Complete results
```

### Checkpoint Contents

Each checkpoint includes:
- Current turn number
- All agent states
- Global state
- Reasoning chains (for LLM agents)
- Metadata (timestamp, schema hash)

### Loading Checkpoints

```python
from llm_sim.persistence import CheckpointManager

manager = CheckpointManager(output_dir="output/run_20231101_123456")
state = manager.load_checkpoint("last")
```

---

## Complete Examples

### Example 1: Simple Economic Simulation

```yaml
simulation:
  name: "Simple Economy"
  max_turns: 50
  checkpoint_interval: 10

state_variables:
  agent_vars:
    wealth:
      type: float
      min: 0
      default: 1000.0

  global_vars:
    interest_rate:
      type: float
      default: 0.05

agents:
  - name: Trader1
    type: llm_agent
  - name: Trader2
    type: llm_agent

engine:
  type: economic_engine

validator:
  type: llm_validator
  config:
    permissive: false

llm:
  model: "llama3.2"
  host: "http://localhost:11434"

logging:
  level: "INFO"
```

### Example 2: Partial Observability Scenario

```yaml
simulation:
  name: "Intelligence Game"
  max_turns: 100
  checkpoint_interval: 20

state_variables:
  agent_vars:
    economic_strength:
      type: float
      min: 0
      default: 1000.0

    military_power:
      type: float
      min: 0
      default: 100.0

    secret_operations:
      type: int
      default: 0

    intelligence_level:
      type: int
      min: 0
      max: 10
      default: 5

  global_vars:
    global_tension:
      type: float
      min: 0.0
      max: 1.0
      default: 0.3

agents:
  - name: Nation1
    type: llm_agent

  - name: Nation2
    type: llm_agent

  - name: Spy
    type: llm_agent

engine:
  type: geopolitical_engine

validator:
  type: llm_validator

observability:
  enabled: true

  variable_visibility:
    external:
      - economic_strength
      - military_power

    internal:
      - secret_operations
      - intelligence_level

  matrix:
    # Nation1 sees self and public info of Nation2
    - [Nation1, Nation1, insider, 0.0]
    - [Nation1, Nation2, external, 0.2]
    - [Nation1, Spy, unaware, null]
    - [Nation1, global, external, 0.1]

    # Nation2 similar
    - [Nation2, Nation2, insider, 0.0]
    - [Nation2, Nation1, external, 0.2]
    - [Nation2, Spy, unaware, null]
    - [Nation2, global, external, 0.1]

    # Spy has insider access to Nation1
    - [Spy, Spy, insider, 0.0]
    - [Spy, Nation1, insider, 0.05]
    - [Spy, Nation2, external, 0.15]
    - [Spy, global, insider, 0.0]

  default:
    level: unaware
    noise: 0.0

llm:
  model: "llama3.3:70b"
  host: "http://localhost:11434"
  temperature: 0.8

logging:
  level: "DEBUG"
  format: "json"
```

### Example 3: Market Competition

```yaml
simulation:
  name: "Market Competition"
  max_turns: 200
  checkpoint_interval: 25

state_variables:
  agent_vars:
    market_share:
      type: float
      min: 0.0
      max: 1.0
      default: 0.1

    product_quality:
      type: float
      min: 0.0
      max: 10.0
      default: 5.0

    rd_investment:
      type: float
      min: 0.0
      default: 100.0

    pricing_strategy:
      type: str
      default: "moderate"

    # Private information
    cost_structure:
      type: float
      default: 50.0

    secret_innovation:
      type: int
      default: 0

  global_vars:
    market_demand:
      type: float
      default: 1000.0

    average_price:
      type: float
      default: 100.0

agents:
  - name: Company1
    type: llm_agent
    config:
      strategy: "cost_leader"

  - name: Company2
    type: llm_agent
    config:
      strategy: "differentiator"

  - name: Company3
    type: llm_agent
    config:
      strategy: "innovator"

engine:
  type: market_engine
  config:
    elasticity: 1.5
    innovation_rate: 0.1

validator:
  type: market_validator
  config:
    permissive: false

observability:
  enabled: true

  variable_visibility:
    external:
      - market_share
      - product_quality
      - pricing_strategy

    internal:
      - rd_investment
      - cost_structure
      - secret_innovation

  matrix:
    # Each company sees competitors' public data with noise
    - [Company1, Company1, insider, 0.0]
    - [Company1, Company2, external, 0.15]
    - [Company1, Company3, external, 0.15]
    - [Company1, global, external, 0.05]

    - [Company2, Company2, insider, 0.0]
    - [Company2, Company1, external, 0.15]
    - [Company2, Company3, external, 0.15]
    - [Company2, global, external, 0.05]

    - [Company3, Company3, insider, 0.0]
    - [Company3, Company1, external, 0.15]
    - [Company3, Company2, external, 0.15]
    - [Company3, global, external, 0.05]

  default:
    level: external
    noise: 0.2

llm:
  model: "gpt-4"
  host: "https://api.openai.com/v1"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7

logging:
  level: "INFO"
  format: "json"
```

---

## Configuration Validation

The framework validates configurations on load:

### Common Validation Errors

**1. Unknown variable in observability:**
```yaml
variable_visibility:
  external: [unknown_var]  # ERROR: not in state_variables
```

**2. Variable in both external and internal:**
```yaml
variable_visibility:
  external: [wealth]
  internal: [wealth]  # ERROR: cannot be both
```

**3. Unknown agent in matrix:**
```yaml
matrix:
  - [UnknownAgent, Agent1, external, 0.1]  # ERROR: agent not defined
```

**4. Negative noise:**
```yaml
matrix:
  - [Agent1, Agent2, external, -0.1]  # ERROR: noise must be >= 0
```

**5. Invalid observability level:**
```yaml
matrix:
  - [Agent1, Agent2, public, 0.1]  # ERROR: must be unaware/external/insider
```

---

## Best Practices

### 1. Start Simple

Begin with basic configuration, add observability later:

```yaml
# Phase 1: Basic simulation
agents:
  - name: Agent1
    type: my_agent

# Phase 2: Add observability
observability:
  enabled: true
  # ...
```

### 2. Use Meaningful Noise Levels

| Noise | Interpretation | Use Case |
|-------|----------------|----------|
| 0.0 | Perfect information | Insider, own state |
| 0.05 | High quality intel | Spy networks, allies |
| 0.1-0.2 | Public information | Market data, news |
| 0.3+ | Low quality intel | Rumors, distant observations |

### 3. Leverage Defaults

Use sparse matrix + default for cleaner config:

```yaml
matrix:
  # Only specify special relationships
  - [Agent1, Agent1, insider, 0.0]
  - [Spy, Target, insider, 0.05]

default:
  level: external  # Everyone else gets external view
  noise: 0.2
```

### 4. Test Incrementally

1. Test with `enabled: false` (full observability)
2. Enable observability with low noise
3. Gradually increase noise and restrictions
4. Verify agent behavior changes appropriately

### 5. Document Your Schema

Add descriptions to variables:

```yaml
state_variables:
  agent_vars:
    economic_strength:
      type: float
      default: 1000.0
      description: "Agent's total economic power in GDP units"
```

### 6. Use Structured Logging

Enable DEBUG logging to see observations:

```yaml
logging:
  level: "DEBUG"
  format: "json"
```

Look for events:
- `observation_construction` - When observations are built
- `observation_filtered.agents_filtered` - Which agents are visible
- `noise_applied` - Noise application details

---

## Troubleshooting

### Agents See Everything Despite Observability

**Problem:** Observability enabled but agents still see full state

**Solutions:**
1. Check `observability.enabled: true`
2. Verify matrix entries exist for observer-target pairs
3. Check default level isn't `insider`
4. Review logs for `observation_filtered` events

### Noise Not Applied

**Problem:** Observed values identical to ground truth

**Solutions:**
1. Verify `noise > 0.0` in matrix entries
2. Check variable is numeric (noise only applies to int/float)
3. For integers, noise may round to same value (expected)

### Matrix Too Complex

**Problem:** Too many matrix entries to maintain

**Solutions:**
1. Use `default` for common cases
2. Group agents by role with same observability patterns
3. Consider if full asymmetry is needed

### Variables Missing in Observations

**Problem:** Expected variables not in observation

**Solutions:**
1. Check variable is in `external` list for external observers
2. Verify observability level is correct
3. For `unaware`, entire agent is excluded (expected)

---

## Next Steps

- **[API Reference](API.md)** - Extending the framework
- **[LLM Setup](LLM_SETUP.md)** - Configuring LLM providers
- **[Platform Architecture](PLATFORM_ARCHITECTURE.md)** - Multi-simulation orchestration
- **[Example Implementation](https://github.com/your-org/llm-sim-economic)** - Complete reference

---

**Need help?** Check existing configurations in the `scenarios/` directory of example implementations.
