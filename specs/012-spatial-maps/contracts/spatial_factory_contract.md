# Contract: SpatialStateFactory Interface

**Feature**: 012-spatial-maps
**Component**: SpatialStateFactory (topology creation from config)
**Location**: `src/llm_sim/infrastructure/spatial/factory.py`

## Purpose

Defines the contract for creating initial SpatialState instances from various topology configurations.

## Contract Requirements

### General Factory Requirements
- All factory methods MUST be static (`@staticmethod`)
- All factory methods MUST return valid SpatialState instance
- All factory methods MUST initialize "default" network
- All factory methods MUST validate configuration before creation
- All factory methods MUST raise clear errors for invalid configs

### Main Dispatcher

**FR-002-005: create**
```python
@staticmethod
def create(config: SpatialConfig) -> SpatialState:
    """Create SpatialState from config by dispatching to specific factory.

    Contract:
    - MUST dispatch to correct factory based on config.topology.type
    - MUST support: "grid", "hex_grid", "network", "geojson"
    - MUST raise ValueError for unknown topology types
    - MUST return valid SpatialState instance
    - MUST apply location_attributes from config if provided
    - MUST create additional_networks from config if provided
    """
```

### Grid Topology Factory

**FR-002: from_grid_config**
```python
@staticmethod
def from_grid_config(config: GridConfig) -> SpatialState:
    """Build 2D square grid topology.

    Contract:
    - MUST create width × height locations
    - MUST use "{x},{y}" as location IDs (0-indexed)
    - MUST create "default" network with grid adjacency
    - MUST respect connectivity (4-way or 8-way neighbors)
    - MUST handle wrapping if config.wrapping=True (toroidal grid)
    - MUST initialize empty agent_positions
    - MUST set topology_type="grid"
    - MUST return valid SpatialState

    Grid Coordinates:
    - Origin at (0, 0) top-left
    - X increases right, Y increases down
    - 4-connectivity: (x±1, y) and (x, y±1)
    - 8-connectivity: adds diagonals (x±1, y±1)
    - Wrapping: x % width, y % height
    """
```

**Example Grid**:
```
3x3 grid, 4-connectivity:
(0,0)---(1,0)---(2,0)
  |       |       |
(0,1)---(1,1)---(2,1)
  |       |       |
(0,2)---(1,2)---(2,2)
```

### Hexagonal Grid Factory

**FR-003: from_hex_config**
```python
@staticmethod
def from_hex_config(config: HexGridConfig) -> SpatialState:
    """Build hexagonal grid topology using axial coordinates.

    Contract:
    - MUST use axial coordinates (q, r)
    - MUST create hexagonal grid with given radius
    - MUST use "{q},{r}" as location IDs
    - MUST create "default" network with hex adjacency (6 neighbors)
    - MUST initialize empty agent_positions
    - MUST set topology_type="hex_grid"
    - MUST return valid SpatialState

    Axial Coordinate System:
    - (0, 0) at center
    - 6 neighbors at: (q±1,r), (q,r±1), (q+1,r-1), (q-1,r+1)
    - Radius R: includes all hexes with max(|q|, |r|, |q+r|) <= R
    """
```

**Example Hex Grid** (radius=1):
```
     (-1,1)  (0,1)
  (-1,0)  (0,0)  (1,0)
     (0,-1) (1,-1)
```

### Network/Graph Factory

**FR-004: from_network_config**
```python
@staticmethod
def from_network_config(config: NetworkConfig) -> SpatialState:
    """Build arbitrary graph topology from edge list file.

    Contract:
    - MUST load edges from JSON file at config.edges_file
    - MUST expect JSON format: {"nodes": ["a", "b", "c"], "edges": [["a","b"], ["b","c"]]}
    - MUST create location for each node in "nodes" list
    - MUST create "default" network with edges from "edges" list
    - MUST raise ValueError if file not found
    - MUST raise ValueError if JSON malformed
    - MUST initialize empty agent_positions
    - MUST set topology_type="network"
    - MUST return valid SpatialState

    JSON File Format:
    {
      "nodes": ["node1", "node2", "node3"],
      "edges": [
        ["node1", "node2"],
        ["node2", "node3"]
      ],
      "attributes": {  // Optional
        "node1": {"resource": 100},
        "node2": {"resource": 50}
      }
    }
    """
```

### GeoJSON Factory

**FR-005: from_geojson**
```python
@staticmethod
def from_geojson(config: GeoJSONConfig) -> SpatialState:
    """Load geographic regions from GeoJSON file.

    Contract:
    - MUST load GeoJSON from file at config.geojson_file
    - MUST create location for each Feature in FeatureCollection
    - MUST use feature.properties.name as location ID
    - MUST copy feature.properties to location.attributes
    - MUST compute adjacency from geometry (polygons that touch)
    - MUST create "default" network with computed adjacency
    - MUST raise ValueError if file not found
    - MUST raise ValueError if GeoJSON malformed
    - MUST raise ValueError if features missing "name" property
    - MUST initialize empty agent_positions
    - MUST set topology_type="regions"
    - MUST return valid SpatialState

    GeoJSON Requirements:
    - Type: "FeatureCollection"
    - Each Feature must have properties.name (unique)
    - Geometry: Polygon or MultiPolygon
    - Adjacency: Two polygons adjacent if they touch or share boundary
    """
```

**Example GeoJSON**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "winterfell",
        "loyalty": "stark",
        "population": 100000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]
      }
    }
  ]
}
```

## Configuration Post-Processing

### Apply Location Attributes

After topology creation, if `config.location_attributes` provided:
```python
def _apply_location_attributes(
    spatial_state: SpatialState,
    location_attributes: Dict[str, Dict[str, Any]]
) -> SpatialState:
    """Override/augment location attributes from config.

    Contract:
    - MUST merge attributes into existing location.attributes
    - MUST skip locations not in spatial_state.locations (warn)
    - MUST preserve existing attributes not in config
    - MUST overwrite attributes specified in config
    """
```

### Create Additional Networks

After topology creation, if `config.additional_networks` provided:
```python
def _create_additional_networks(
    spatial_state: SpatialState,
    networks: List[Dict[str, Any]]
) -> SpatialState:
    """Add extra network layers beyond base topology.

    Contract:
    - MUST load each network definition
    - MUST validate network edges reference valid locations
    - MUST add NetworkState to spatial_state.networks
    - MUST preserve existing networks (including "default")

    Network Definition Format:
    {
      "name": "rail",
      "edges_file": "path/to/rail_edges.json"
    }
    """
```

## Test Requirements

Each factory method MUST have:
1. **Valid config test** - Returns SpatialState for valid input
2. **Topology correctness test** - Verifies locations and edges correct
3. **Invalid config test** - Raises appropriate error for invalid input
4. **File loading test** - Handles missing/malformed files (for network/geojson)
5. **Attribute application test** - location_attributes merged correctly
6. **Additional network test** - Extra networks added correctly
7. **Default network test** - "default" network always created
8. **Empty config test** - Handles minimal valid config

## Validation Strategy

**Pre-creation validation**:
- Config file paths must exist and be readable
- Config parameters must be in valid ranges (width > 0, radius > 0)
- JSON/GeoJSON files must be well-formed

**Post-creation validation**:
- Returned SpatialState must pass Pydantic validation
- "default" network must exist in networks dict
- All edge references must point to valid location IDs
- topology_type must match config type

## Error Messages

Error messages MUST include:
- What creation failed
- What was invalid in config
- Expected format or value range
- Path to fix the issue

**Example**:
```python
raise ValueError(
    f"Failed to create grid topology: width must be positive, got {config.width}. "
    f"Remediation: Set spatial.topology.width to positive integer in config."
)
```

## Performance Expectations

- from_grid_config: O(W × H) where W=width, H=height
- from_hex_config: O(R²) where R=radius
- from_network_config: O(N + E) where N=nodes, E=edges
- from_geojson: O(R² × C) where R=regions, C=polygon complexity (adjacency computation)
