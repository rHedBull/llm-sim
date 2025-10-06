# Contract: SpatialMutations Interface

**Feature**: 012-spatial-maps
**Component**: SpatialMutations (write operations for engines)
**Location**: `src/llm_sim/infrastructure/spatial/mutations.py`

## Purpose

Defines the contract for spatial state mutation operations available exclusively to engines.

## Contract Requirements

### General Requirements
- All methods MUST be static (`@staticmethod`)
- All methods MUST return new SpatialState instance (immutable updates)
- All methods MUST NOT mutate input spatial_state
- All methods MUST preserve unaffected state fields
- All methods MUST validate inputs and raise clear errors for invalid operations
- All methods MUST handle edge cases gracefully

### Agent Movement

**FR-030: move_agent**
```python
@staticmethod
def move_agent(
    spatial_state: SpatialState,
    agent_name: str,
    new_location: str
) -> SpatialState:
    """Move agent to new location.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST update agent_positions[agent_name] = new_location
    - MUST add agent if not previously positioned
    - MUST raise ValueError if new_location not in locations
    - MUST preserve all other fields (locations, networks, connections)
    """
```

**FR-031: move_agents_batch**
```python
@staticmethod
def move_agents_batch(
    spatial_state: SpatialState,
    moves: Dict[str, str]
) -> SpatialState:
    """Move multiple agents at once.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST apply all moves atomically
    - MUST validate all target locations exist before applying any move
    - MUST raise ValueError if any location invalid (no partial updates)
    - MUST preserve relative atomicity (all or nothing validation)
    """
```

### Location Updates

**FR-032: set_location_attribute**
```python
@staticmethod
def set_location_attribute(
    spatial_state: SpatialState,
    location: str,
    key: str,
    value: Any
) -> SpatialState:
    """Set attribute value for location.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST update locations[location].attributes[key] = value
    - MUST raise ValueError if location not in locations
    - MUST create new LocationState with updated attributes
    - MUST preserve all other location attributes
    - MUST preserve all other state fields
    """
```

**FR-032: update_location_attributes**
```python
@staticmethod
def update_location_attributes(
    spatial_state: SpatialState,
    location: str,
    updates: Dict[str, Any]
) -> SpatialState:
    """Update multiple attributes for location.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST merge updates into location.attributes
    - MUST raise ValueError if location not in locations
    - MUST preserve existing attributes not in updates
    - MUST overwrite attributes that are in updates
    """
```

### Network Modifications

**FR-033: add_connection**
```python
@staticmethod
def add_connection(
    spatial_state: SpatialState,
    loc1: str,
    loc2: str,
    network: str,
    attributes: Optional[Dict[str, Any]] = None
) -> SpatialState:
    """Add connection to network.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST add (loc1, loc2) to networks[network].edges
    - MUST raise ValueError if either location not in locations
    - MUST raise ValueError if network not in networks
    - MUST create connection in connections dict if attributes provided
    - MUST handle bidirectional connections (add both directions to edges)
    """
```

**FR-034: remove_connection**
```python
@staticmethod
def remove_connection(
    spatial_state: SpatialState,
    loc1: str,
    loc2: str,
    network: str
) -> SpatialState:
    """Remove connection from network.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST remove (loc1, loc2) from networks[network].edges
    - MUST handle both (loc1, loc2) and (loc2, loc1) for bidirectional
    - MUST not raise error if connection doesn't exist (idempotent)
    - MUST remove from connections dict if present
    """
```

**FR-035: update_connection_attribute**
```python
@staticmethod
def update_connection_attribute(
    spatial_state: SpatialState,
    loc1: str,
    loc2: str,
    key: str,
    value: Any
) -> SpatialState:
    """Update connection attribute.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST update connections[(loc1, loc2)].attributes[key] = value
    - MUST raise ValueError if connection not in connections
    - MUST preserve other connection attributes
    - MUST handle both (loc1, loc2) and (loc2, loc1) keys
    """
```

### Network Management

**FR-036: create_network**
```python
@staticmethod
def create_network(
    spatial_state: SpatialState,
    network_name: str,
    edges: Optional[Set[Tuple[str, str]]] = None
) -> SpatialState:
    """Create new network layer.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST add NetworkState to networks[network_name]
    - MUST raise ValueError if network_name already exists
    - MUST validate all edge locations exist
    - MUST initialize with empty edges if edges=None
    """
```

**FR-037: remove_network**
```python
@staticmethod
def remove_network(
    spatial_state: SpatialState,
    network_name: str
) -> SpatialState:
    """Remove network layer.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST remove networks[network_name]
    - MUST not raise error if network doesn't exist (idempotent)
    - MUST NOT remove connections (connections are independent)
    - MUST raise ValueError if removing "default" network
    """
```

### Batch Operations

**FR-038: apply_to_region**
```python
@staticmethod
def apply_to_region(
    spatial_state: SpatialState,
    locations: List[str],
    update_fn: Callable[[LocationState], Dict[str, Any]]
) -> SpatialState:
    """Apply update function to all locations in region.

    Contract:
    - MUST return new SpatialState instance
    - MUST NOT mutate input spatial_state
    - MUST apply update_fn to each location in locations list
    - MUST merge returned dict into location.attributes
    - MUST raise ValueError if any location not in locations
    - MUST validate all locations exist before applying updates
    - MUST preserve locations not in list unchanged
    """
```

## Test Requirements

Each mutation method MUST have:
1. **Immutability test** - Verify input spatial_state unchanged after call
2. **Return type test** - Verify returns new SpatialState instance
3. **Update correctness test** - Verify intended change applied
4. **Preservation test** - Verify unaffected fields unchanged
5. **Error handling test** - Verify raises appropriate errors for invalid inputs
6. **Edge case tests** - Empty updates, non-existent items, etc.

## Validation Strategy

**Pre-condition checks** (raise ValueError):
- Location IDs must exist in spatial_state.locations
- Network names must exist in spatial_state.networks
- Attribute values must be JSON-serializable

**Post-condition guarantees**:
- Returned SpatialState is valid (passes Pydantic validation)
- Input spatial_state is unchanged
- Only intended modifications applied

## Error Messages

Error messages MUST include:
- What operation failed
- What input was invalid
- List of valid alternatives
- How to fix the issue

**Example**:
```python
raise ValueError(
    f"Cannot move agent '{agent_name}' to invalid location '{new_location}'. "
    f"Valid locations: {sorted(spatial_state.locations.keys())}. "
    f"Remediation: Ensure location exists in spatial topology."
)
```

## Performance Expectations

- move_agent: O(1) - dict update
- set_location_attribute: O(1) - dict update + Pydantic model creation
- add_connection: O(1) - set insertion
- create_network: O(E) where E = number of edges
- apply_to_region: O(L * U) where L = locations, U = update_fn cost
