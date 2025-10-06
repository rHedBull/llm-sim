# Contract: SpatialQuery Interface

**Feature**: 012-spatial-maps
**Component**: SpatialQuery (read-only spatial operations)
**Location**: `src/llm_sim/infrastructure/spatial/query.py`

## Purpose

Defines the contract for read-only spatial query operations available to agents, validators, and engines.

## Contract Requirements

### General Requirements
- All methods MUST be static (`@staticmethod`)
- All methods MUST be pure functions (no side effects)
- All methods MUST handle `None` spatial_state gracefully
- All methods MUST return typed values (explicit type annotations)
- All methods MUST NOT mutate input arguments

### Navigation Queries

**FR-019: get_neighbors**
```python
@staticmethod
def get_neighbors(
    spatial_state: Optional[SpatialState],
    location: str,
    network: str = "default"
) -> List[str]:
    """Get neighboring locations via specified network.

    Contract:
    - MUST return empty list if spatial_state is None
    - MUST return empty list if location not in spatial_state.locations
    - MUST return empty list if network not in spatial_state.networks
    - MUST return list of location IDs connected to given location
    - MUST NOT include location itself in neighbors
    - Order of returned neighbors is unspecified
    """
```

**FR-020: get_distance**
```python
@staticmethod
def get_distance(
    spatial_state: Optional[SpatialState],
    loc1: str,
    loc2: str,
    network: str = "default"
) -> int:
    """Compute distance (hops) between locations.

    Contract:
    - MUST return -1 if spatial_state is None
    - MUST return -1 if either location not found
    - MUST return -1 if network not found
    - MUST return 0 if loc1 == loc2
    - MUST return shortest path length (number of edges)
    - MUST return -1 if no path exists
    """
```

**FR-021: is_adjacent**
```python
@staticmethod
def is_adjacent(
    spatial_state: Optional[SpatialState],
    loc1: str,
    loc2: str,
    network: str = "default"
) -> bool:
    """Check if two locations are directly connected.

    Contract:
    - MUST return False if spatial_state is None
    - MUST return False if either location not found
    - MUST return False if network not found
    - MUST return True if (loc1, loc2) or (loc2, loc1) in network edges
    - MUST return True if loc1 == loc2
    """
```

**FR-022: shortest_path**
```python
@staticmethod
def shortest_path(
    spatial_state: Optional[SpatialState],
    loc1: str,
    loc2: str,
    network: str = "default"
) -> List[str]:
    """Find shortest path between locations.

    Contract:
    - MUST return empty list if spatial_state is None
    - MUST return empty list if either location not found
    - MUST return empty list if network not found
    - MUST return [loc1] if loc1 == loc2
    - MUST return list starting with loc1 and ending with loc2
    - MUST return empty list if no path exists
    - Returned path MUST only include locations connected in network
    """
```

### Agent Position Queries

**FR-018: get_agent_position**
```python
@staticmethod
def get_agent_position(
    spatial_state: Optional[SpatialState],
    agent_name: str
) -> Optional[str]:
    """Get agent's current location.

    Contract:
    - MUST return None if spatial_state is None
    - MUST return None if agent_name not in agent_positions
    - MUST return location ID as string
    - MUST NOT mutate spatial_state
    """
```

**FR-023: get_agents_at**
```python
@staticmethod
def get_agents_at(
    spatial_state: Optional[SpatialState],
    location: str
) -> List[str]:
    """Get all agents at a specific location.

    Contract:
    - MUST return empty list if spatial_state is None
    - MUST return empty list if location not found
    - MUST return list of agent names positioned at location
    - Order of returned agents is unspecified
    """
```

**FR-024: get_agents_within**
```python
@staticmethod
def get_agents_within(
    spatial_state: Optional[SpatialState],
    location: str,
    radius: int,
    network: str = "default"
) -> List[str]:
    """Get agents within radius hops of location.

    Contract:
    - MUST return empty list if spatial_state is None
    - MUST return empty list if location not found
    - MUST include agents at location itself (radius 0)
    - MUST include agents at distance <= radius
    - MUST use specified network for distance calculation
    - Order of returned agents is unspecified
    """
```

### Location Attribute Queries

**FR-025: get_location_attribute**
```python
@staticmethod
def get_location_attribute(
    spatial_state: Optional[SpatialState],
    location: str,
    key: str
) -> Optional[Any]:
    """Get attribute value for location.

    Contract:
    - MUST return None if spatial_state is None
    - MUST return None if location not found
    - MUST return None if key not in location.attributes
    - MUST return attribute value if key exists
    - MUST NOT mutate spatial_state
    """
```

**FR-026: get_locations_by_attribute**
```python
@staticmethod
def get_locations_by_attribute(
    spatial_state: Optional[SpatialState],
    key: str,
    value: Any
) -> List[str]:
    """Find all locations where attribute matches value.

    Contract:
    - MUST return empty list if spatial_state is None
    - MUST return list of location IDs where location.attributes[key] == value
    - MUST handle missing key gracefully (skip location)
    - Order of returned locations is unspecified
    """
```

### Network/Connection Queries

**FR-027: has_connection**
```python
@staticmethod
def has_connection(
    spatial_state: Optional[SpatialState],
    loc1: str,
    loc2: str,
    network: str
) -> bool:
    """Check if connection exists in network.

    Contract:
    - MUST return False if spatial_state is None
    - MUST return False if network not found
    - MUST return True if (loc1, loc2) or (loc2, loc1) in network edges
    - MUST return True if loc1 == loc2 (location connected to itself)
    """
```

**FR-028: get_connection_attribute**
```python
@staticmethod
def get_connection_attribute(
    spatial_state: Optional[SpatialState],
    loc1: str,
    loc2: str,
    key: str
) -> Optional[Any]:
    """Get attribute value for connection.

    Contract:
    - MUST return None if spatial_state is None
    - MUST return None if connection (loc1, loc2) not in connections
    - MUST return None if key not in connection.attributes
    - MUST check both (loc1, loc2) and (loc2, loc1) for bidirectional
    - MUST return attribute value if key exists
    """
```

### Filtering Operations

**FR-042: filter_state_by_proximity**
```python
@staticmethod
def filter_state_by_proximity(
    agent_name: str,
    state: SimulationState,
    radius: int,
    network: str = "default"
) -> SimulationState:
    """Return filtered state containing only nearby agents/locations.

    Contract:
    - MUST return unmodified state if state.spatial_state is None
    - MUST return state with filtered agents dict (only nearby agents)
    - MUST return state with filtered spatial_state.locations (only nearby)
    - MUST include agent's own location and agents at same location
    - MUST preserve global_state unchanged
    - MUST preserve all other state fields unchanged
    - MUST use immutable updates (model_copy)
    """
```

## Test Requirements

Each contract method MUST have:
1. **Happy path test** - Normal operation with valid inputs
2. **None handling test** - spatial_state=None returns safe default
3. **Missing data test** - Handles missing locations/agents gracefully
4. **Edge case tests** - Empty results, self-references, etc.
5. **Immutability test** - Verify no input mutation occurs

## Error Handling

- Methods MUST NOT raise exceptions for missing data (return empty/None)
- Methods MUST raise TypeError for invalid argument types
- Methods MUST raise ValueError only for truly invalid inputs (negative radius, etc.)

## Performance Expectations

- get_agent_position: O(1)
- get_neighbors: O(1) amortized (direct lookup in adjacency)
- get_distance: O(E log V) worst case (NetworkX shortest path)
- get_agents_at: O(A) where A = number of agents
- filter_state_by_proximity: O(A + L) where L = number of locations
