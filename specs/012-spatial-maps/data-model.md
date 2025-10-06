# Data Model: Spatial Positioning and Topology

**Feature**: 012-spatial-maps
**Date**: 2025-10-06

## Overview

This document defines the Pydantic data models for spatial state representation. All models are immutable (frozen=True) and JSON-serializable for checkpoint persistence.

---

## Core Spatial Models

### 1. LocationState

Represents a single location/position in the spatial topology.

**Fields**:
- `id: str` - Unique location identifier (e.g., "5,10" for grid, "winterfell" for region)
- `attributes: Dict[str, Any]` - Arbitrary location properties (resources, terrain, population, etc.)
- `metadata: Dict[str, Any]` - Optional metadata (coordinates, geometry data, etc.)

**Validation**:
- `id` must be non-empty string
- `attributes` and `metadata` must be JSON-serializable

**Pydantic Model**:
```python
class LocationState(BaseModel):
    """State for a single location in spatial topology."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    id: str = Field(..., min_length=1, description="Unique location identifier")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Location attributes (resources, terrain, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (coordinates, geometry, etc.)"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Location id must be non-empty")
        return v.strip()
```

**Example**:
```python
location = LocationState(
    id="winterfell",
    attributes={
        "loyalty": "stark",
        "military_strength": 5000,
        "resources": 1000,
        "terrain": "forest"
    },
    metadata={"region": "north"}
)
```

---

### 2. ConnectionState

Represents a connection/edge between two locations.

**Fields**:
- `type: str` - Connection type (e.g., "border", "road", "rail", "trade_route")
- `attributes: Dict[str, Any]` - Connection properties (speed, capacity, cost, etc.)
- `bidirectional: bool` - Whether connection works both ways

**Validation**:
- `type` must be non-empty string
- `attributes` must be JSON-serializable

**Pydantic Model**:
```python
class ConnectionState(BaseModel):
    """State for a connection between locations."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    type: str = Field(..., min_length=1, description="Connection type")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connection attributes (speed, capacity, cost, etc.)"
    )
    bidirectional: bool = Field(
        default=True,
        description="Whether connection is bidirectional"
    )

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Connection type must be non-empty")
        return v.strip()
```

**Example**:
```python
connection = ConnectionState(
    type="rail",
    attributes={
        "speed": 100,
        "capacity": 1000,
        "travel_time_days": 14
    },
    bidirectional=True
)
```

---

### 3. NetworkState

Represents a network layer (set of connections between locations).

**Fields**:
- `name: str` - Network identifier (e.g., "borders", "rail_network", "trade_routes")
- `edges: Set[Tuple[str, str]]` - Set of location ID pairs representing connections
- `attributes: Dict[str, Any]` - Network-level attributes (optional)

**Validation**:
- `name` must be non-empty string
- Edge tuples must contain two non-empty strings

**Pydantic Model**:
```python
class NetworkState(BaseModel):
    """State for a network layer connecting locations."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    name: str = Field(..., min_length=1, description="Network identifier")
    edges: Set[Tuple[str, str]] = Field(
        default_factory=set,
        description="Set of (location_id, location_id) tuples"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Network-level attributes"
    )

    @field_serializer('edges')
    def serialize_edges(self, edges: Set[Tuple[str, str]], _info):
        """Serialize edges as sorted list for determinism."""
        return sorted([list(edge) for edge in edges])

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Network name must be non-empty")
        return v.strip()

    @field_validator('edges')
    @classmethod
    def validate_edges(cls, v: Set[Tuple[str, str]]) -> Set[Tuple[str, str]]:
        for edge in v:
            if len(edge) != 2:
                raise ValueError(f"Edge must be 2-tuple, got {len(edge)}")
            if not edge[0] or not edge[1]:
                raise ValueError(f"Edge locations must be non-empty: {edge}")
        return v
```

**Example**:
```python
network = NetworkState(
    name="borders",
    edges={
        ("winterfell", "riverlands"),
        ("riverlands", "kings_landing"),
        ("kings_landing", "stormlands")
    },
    attributes={"type": "political_borders"}
)
```

---

### 4. SpatialState

Top-level spatial state containing all spatial information.

**Fields**:
- `topology_type: Literal["grid", "hex_grid", "network", "regions"]` - Type of spatial topology
- `agent_positions: Dict[str, str]` - Maps agent name to location ID
- `locations: Dict[str, LocationState]` - Maps location ID to location state
- `connections: Dict[Tuple[str, str], ConnectionState]` - Maps location pairs to connection state
- `networks: Dict[str, NetworkState]` - Maps network name to network state

**Validation**:
- `topology_type` must be one of the supported types
- Agent positions must reference valid location IDs
- Network edges must reference valid location IDs

**Pydantic Model**:
```python
from typing import Literal, Dict, Tuple

class SpatialState(BaseModel):
    """Complete spatial state for simulation."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    topology_type: Literal["grid", "hex_grid", "network", "regions"] = Field(
        ...,
        description="Type of spatial topology"
    )
    agent_positions: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps agent name to location ID"
    )
    locations: Dict[str, LocationState] = Field(
        default_factory=dict,
        description="Maps location ID to location state"
    )
    connections: Dict[Tuple[str, str], ConnectionState] = Field(
        default_factory=dict,
        description="Maps (loc1, loc2) to connection state"
    )
    networks: Dict[str, NetworkState] = Field(
        default_factory=dict,
        description="Maps network name to network state"
    )

    @field_serializer('agent_positions')
    def serialize_agent_positions(self, positions: Dict[str, str], _info):
        """Serialize with sorted keys for determinism."""
        return dict(sorted(positions.items()))

    @field_serializer('connections')
    def serialize_connections(self, connections: Dict[Tuple[str, str], ConnectionState], _info):
        """Serialize connection keys as sorted list of tuples."""
        return {
            f"{loc1},{loc2}": conn.model_dump()
            for (loc1, loc2), conn in sorted(connections.items())
        }

    @model_validator(mode='after')
    def validate_references(self) -> 'SpatialState':
        """Validate that agent positions and network edges reference valid locations."""
        valid_locations = set(self.locations.keys())

        # Validate agent positions
        for agent_name, location_id in self.agent_positions.items():
            if location_id not in valid_locations:
                raise ValueError(
                    f"Agent '{agent_name}' positioned at invalid location '{location_id}'. "
                    f"Valid locations: {sorted(valid_locations)}"
                )

        # Validate network edges
        for network_name, network_state in self.networks.items():
            for loc1, loc2 in network_state.edges:
                if loc1 not in valid_locations:
                    raise ValueError(
                        f"Network '{network_name}' references invalid location '{loc1}'"
                    )
                if loc2 not in valid_locations:
                    raise ValueError(
                        f"Network '{network_name}' references invalid location '{loc2}'"
                    )

        # Validate connections reference valid locations
        for (loc1, loc2) in self.connections.keys():
            if loc1 not in valid_locations or loc2 not in valid_locations:
                raise ValueError(
                    f"Connection ({loc1}, {loc2}) references invalid location"
                )

        return self
```

**Example**:
```python
spatial_state = SpatialState(
    topology_type="regions",
    agent_positions={
        "house_stark": "winterfell",
        "house_lannister": "casterly_rock"
    },
    locations={
        "winterfell": LocationState(id="winterfell", attributes={"loyalty": "stark"}),
        "casterly_rock": LocationState(id="casterly_rock", attributes={"loyalty": "lannister"})
    },
    connections={
        ("winterfell", "riverlands"): ConnectionState(type="border", bidirectional=True)
    },
    networks={
        "borders": NetworkState(name="borders", edges={("winterfell", "riverlands")})
    }
)
```

---

## Configuration Models

### 5. GridConfig

Configuration for 2D square grid topology.

**Fields**:
- `type: Literal["grid"]` - Must be "grid"
- `width: int` - Grid width (positive)
- `height: int` - Grid height (positive)
- `connectivity: Literal[4, 8]` - Neighbor connectivity (4-way or 8-way)
- `wrapping: bool` - Whether grid wraps (toroidal)

**Pydantic Model**:
```python
class GridConfig(BaseModel):
    """Configuration for 2D grid topology."""
    type: Literal["grid"] = "grid"
    width: int = Field(..., gt=0, description="Grid width")
    height: int = Field(..., gt=0, description="Grid height")
    connectivity: Literal[4, 8] = Field(default=4, description="Neighbor connectivity")
    wrapping: bool = Field(default=False, description="Whether grid wraps (toroidal)")
```

---

### 6. HexGridConfig

Configuration for hexagonal grid topology.

**Fields**:
- `type: Literal["hex_grid"]` - Must be "hex_grid"
- `radius: int` - Hex grid radius (creates hexagonal grid)
- `coord_system: Literal["axial"]` - Coordinate system (axial only for now)

**Pydantic Model**:
```python
class HexGridConfig(BaseModel):
    """Configuration for hexagonal grid topology."""
    type: Literal["hex_grid"] = "hex_grid"
    radius: int = Field(..., gt=0, description="Hex grid radius")
    coord_system: Literal["axial"] = Field(default="axial", description="Coordinate system")
```

---

### 7. NetworkConfig

Configuration for network/graph topology loaded from file.

**Fields**:
- `type: Literal["network"]` - Must be "network"
- `edges_file: str` - Path to JSON file with edge list

**Pydantic Model**:
```python
class NetworkConfig(BaseModel):
    """Configuration for network/graph topology."""
    type: Literal["network"] = "network"
    edges_file: str = Field(..., description="Path to JSON edge list file")

    @field_validator('edges_file')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"Edges file not found: {v}")
        return v
```

---

### 8. GeoJSONConfig

Configuration for geographic region topology from GeoJSON.

**Fields**:
- `type: Literal["geojson"]` - Must be "geojson"
- `geojson_file: str` - Path to GeoJSON file

**Pydantic Model**:
```python
class GeoJSONConfig(BaseModel):
    """Configuration for GeoJSON topology."""
    type: Literal["geojson"] = "geojson"
    geojson_file: str = Field(..., description="Path to GeoJSON file")

    @field_validator('geojson_file')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"GeoJSON file not found: {v}")
        return v
```

---

### 9. SpatialConfig

Top-level spatial configuration (union of all topology configs).

**Fields**:
- Union of GridConfig | HexGridConfig | NetworkConfig | GeoJSONConfig
- `location_attributes: Optional[Dict[str, Dict[str, Any]]]` - Initial location attributes
- `networks: Optional[List[Dict]]` - Additional network layers

**Pydantic Model**:
```python
from typing import Union, Optional, List

SpatialConfigTypes = Union[GridConfig, HexGridConfig, NetworkConfig, GeoJSONConfig]

class SpatialConfig(BaseModel):
    """Top-level spatial configuration."""
    topology: SpatialConfigTypes = Field(..., discriminator='type')
    location_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Initial attributes per location"
    )
    additional_networks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Additional network layers beyond base topology"
    )
```

---

### 10. AgentConfig Extension

Add `initial_location` field to existing AgentConfig.

**Addition**:
```python
class AgentConfig(BaseModel):
    """Agent configuration (existing fields + spatial extension)."""
    name: str
    type: str
    initial_economic_strength: Optional[float] = None

    # NEW: Spatial positioning
    initial_location: Optional[str] = Field(
        default=None,
        description="Initial location ID for spatial simulations"
    )
```

---

### 11. SimulationConfig Extension

Add `spatial` field to existing SimulationConfig.

**Addition**:
```python
class SimulationConfig(BaseModel):
    """Complete simulation configuration (existing fields + spatial extension)."""
    simulation: SimulationSettings
    engine: EngineConfig
    agents: List[AgentConfig]
    validator: ValidatorConfig
    logging: Optional[LoggingConfig] = None
    llm: Optional[LLMConfig] = None
    state_variables: Optional[StateVariablesConfig] = None
    observability: Optional[Any] = None

    # NEW: Spatial configuration
    spatial: Optional[SpatialConfig] = Field(
        default=None,
        description="Optional spatial topology configuration"
    )

    @model_validator(mode='after')
    def validate_spatial_agent_locations(self) -> 'SimulationConfig':
        """Validate agent initial_location references valid spatial locations."""
        if self.spatial is None:
            return self

        # Will be validated after SpatialState is created by factory
        # This is a reminder to validate in orchestrator initialization
        return self
```

---

### 12. SimulationState Extension

Add `spatial_state` field to existing SimulationState.

**Addition**:
```python
class SimulationState(BaseModel):
    """Complete simulation state (existing fields + spatial extension)."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    turn: int
    agents: Dict[str, BaseModel]
    global_state: BaseModel
    reasoning_chains: List[LLMReasoningChain] = Field(default_factory=list)
    paused_agents: set[str] = Field(default_factory=set)
    auto_resume: Dict[str, int] = Field(default_factory=dict)

    # NEW: Spatial state
    spatial_state: Optional[SpatialState] = Field(
        default=None,
        description="Optional spatial positioning state"
    )

    @field_serializer('spatial_state')
    def serialize_spatial_state(self, spatial_state: Optional[SpatialState], _info):
        """Serialize spatial_state if present."""
        if spatial_state is None:
            return None
        return spatial_state.model_dump()
```

---

## Relationships

```
SimulationConfig
├── spatial: Optional[SpatialConfig]
│   ├── topology: GridConfig | HexGridConfig | NetworkConfig | GeoJSONConfig
│   ├── location_attributes: Dict[loc_id, attributes]
│   └── additional_networks: List[network_defs]
└── agents: List[AgentConfig]
    └── initial_location: Optional[str]

SimulationState
├── spatial_state: Optional[SpatialState]
│   ├── topology_type: str
│   ├── agent_positions: Dict[agent_name, location_id]
│   ├── locations: Dict[location_id, LocationState]
│   ├── connections: Dict[(loc1, loc2), ConnectionState]
│   └── networks: Dict[network_name, NetworkState]
│       └── edges: Set[(loc1, loc2)]
└── agents: Dict[agent_name, AgentState]
```

---

## File Locations

**State Models**: `src/llm_sim/models/state.py`
- Add: SpatialState, LocationState, NetworkState, ConnectionState
- Update: SimulationState (add spatial_state field)

**Config Models**: `src/llm_sim/models/config.py`
- Add: GridConfig, HexGridConfig, NetworkConfig, GeoJSONConfig, SpatialConfig
- Update: AgentConfig (add initial_location field)
- Update: SimulationConfig (add spatial field)

---

## Next Steps

1. Implement these models in `src/llm_sim/models/state.py` and `src/llm_sim/models/config.py`
2. Write contract tests to verify model behavior
3. Proceed to factory implementation
