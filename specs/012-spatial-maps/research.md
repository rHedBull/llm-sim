# Research: Spatial Positioning and Topology

**Feature**: 012-spatial-maps
**Date**: 2025-10-06
**Status**: Complete

## Research Questions

### 1. NetworkX Integration for Shortest Path

**Question**: How to integrate NetworkX for graph algorithms while maintaining Pydantic immutability?

**Decision**: Use NetworkX as computational engine only, not storage
- Store spatial data in Pydantic models (edge lists as `Set[Tuple[str, str]]`)
- Convert to NetworkX graph on-demand for path computation
- Return pure Python results (lists, integers)
- NetworkX graphs are ephemeral, never stored in state

**Rationale**:
- Pydantic cannot serialize NetworkX graph objects
- Edge list format is simple, JSON-compatible, and sufficient for reconstruction
- NetworkX provides battle-tested shortest path algorithms (Dijkstra, BFS)
- Performance acceptable: constructing graph from edge list is O(E), pathfinding is O(E log V)

**Implementation Pattern**:
```python
@staticmethod
def shortest_path(spatial_state: SpatialState, loc1: str, loc2: str, network: str = "default") -> List[str]:
    """Compute shortest path using NetworkX internally."""
    import networkx as nx

    # Build ephemeral graph from edge list
    network_state = spatial_state.networks[network]
    G = nx.Graph()
    G.add_edges_from(network_state.edges)

    # Compute path
    try:
        path = nx.shortest_path(G, source=loc1, target=loc2)
        return list(path)
    except nx.NetworkXNoPath:
        return []
```

**Alternatives Considered**:
- Custom pathfinding implementation: Rejected - wheel reinvention, more bugs
- Store NetworkX in state: Rejected - not Pydantic-serializable
- Use adjacency matrix: Rejected - space inefficient for sparse graphs

---

### 2. GeoJSON Parsing and Adjacency Computation

**Question**: Best library for parsing GeoJSON and computing polygon adjacency?

**Decision**: Use `shapely` for geometric operations, `geojson` for parsing
- `geojson` library for lightweight JSON parsing and validation
- `shapely` for polygon operations (intersection, touching detection)
- Two polygons are adjacent if they share a border (`.touches()` or `.intersects()` with shared boundary)

**Rationale**:
- `shapely` is industry standard for computational geometry
- `geojson` provides Pythonic GeoJSON parsing with validation
- Both are pure Python/C, no external system dependencies
- Well-documented, actively maintained

**Implementation Pattern**:
```python
def _compute_adjacency_from_geojson(geojson_data: dict) -> Set[Tuple[str, str]]:
    """Compute adjacency from GeoJSON polygon geometries."""
    from shapely.geometry import shape

    # Parse geometries
    regions = {}
    for feature in geojson_data["features"]:
        name = feature["properties"]["name"]
        geom = shape(feature["geometry"])
        regions[name] = geom

    # Compute adjacency
    edges = set()
    for name1, geom1 in regions.items():
        for name2, geom2 in regions.items():
            if name1 < name2:  # Avoid duplicates
                if geom1.touches(geom2) or (geom1.intersects(geom2) and not geom1.equals(geom2)):
                    edges.add((name1, name2))
                    edges.add((name2, name1))  # Bidirectional

    return edges
```

**Alternatives Considered**:
- GDAL/OGR: Rejected - heavy system dependency, overkill for simple adjacency
- Manual coordinate comparison: Rejected - complex, error-prone
- GEOS directly: Rejected - shapely wraps GEOS with better API

---

### 3. Hexagonal Grid Coordinate System

**Question**: Which coordinate system for hexagonal grids (axial, cube, offset)?

**Decision**: **Axial coordinates** (q, r)
- Represent hex positions as (q, r) tuples
- 6 neighbors via simple offset arithmetic
- Straightforward conversion to/from pixel coordinates for visualization

**Rationale**:
- Axial is the standard in game development (see Red Blob Games guide)
- Simpler than cube coordinates (3 components)
- More intuitive than offset coordinates (no odd/even row special casing)
- Distance formula: `max(abs(q1-q2), abs(r1-r2), abs((q1+r1)-(q2+r2)))`

**Implementation Pattern**:
```python
HEX_AXIAL_NEIGHBORS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

def _get_hex_neighbors(q: int, r: int) -> List[str]:
    """Get 6 neighbors of hex at axial coordinates (q, r)."""
    neighbors = []
    for dq, dr in HEX_AXIAL_NEIGHBORS:
        neighbors.append(f"{q+dq},{r+dr}")
    return neighbors
```

**Alternatives Considered**:
- Cube coordinates (x, y, z): Rejected - redundant third component, more storage
- Offset coordinates: Rejected - complex neighbor logic with odd/even row special cases
- Doubled coordinates: Rejected - uncommon, less documented

**Reference**: [Red Blob Games - Hexagonal Grids](https://www.redblobgames.com/grids/hexagons/)

---

### 4. Graph Serialization in Pydantic Models

**Question**: How to serialize graph/network structures for JSON checkpoints?

**Decision**: **Edge list format** stored as `Set[Tuple[str, str]]`
- Networks stored as: `Set[("loc1", "loc2"), ("loc2", "loc3"), ...]`
- Pydantic serializes tuples as JSON arrays: `[["loc1", "loc2"], ["loc2", "loc3"]]`
- Deserialization converts back to set of tuples
- Custom serializer/validator if needed for optimization

**Rationale**:
- Edge list is simplest graph representation
- Native Pydantic support for `Set[Tuple[str, str]]`
- Compact JSON representation
- Easy human inspection and debugging
- Efficient reconstruction (O(E) to build NetworkX graph)

**Implementation Pattern**:
```python
class NetworkState(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    edges: Set[Tuple[str, str]] = Field(default_factory=set)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @field_serializer('edges')
    def serialize_edges(self, edges: Set[Tuple[str, str]], _info):
        """Serialize edges as sorted list for determinism."""
        return sorted([list(edge) for edge in edges])
```

**Alternatives Considered**:
- Adjacency list `Dict[str, List[str]]`: Rejected - harder to ensure symmetry for undirected graphs
- Adjacency matrix: Rejected - O(V²) space, wasteful for sparse graphs
- Graph database: Rejected - over-engineering for this scale
- NetworkX pickle: Rejected - not JSON, not human-readable

---

## Technology Stack Summary

**Dependencies to Add**:
```bash
uv add networkx     # Graph algorithms (shortest path, etc.)
uv add shapely      # Geometric operations for GeoJSON
uv add geojson      # GeoJSON parsing
```

**Existing Dependencies** (already in project):
- Pydantic 2.x - State models
- PyYAML 6.x - Configuration
- structlog 24.x - Logging

**Performance Characteristics**:
- Grid neighbor lookup: O(1) - simple arithmetic
- Hex neighbor lookup: O(1) - 6 offset additions
- Network neighbor lookup: O(1) - set membership
- Shortest path: O(E log V) - NetworkX Dijkstra
- GeoJSON adjacency computation: O(N²) - one-time at initialization
- Serialization: O(E) - edge list iteration

**Constraints Satisfied**:
- ✅ Immutability: NetworkX used only for computation, not storage
- ✅ Serializability: Edge lists are JSON-compatible
- ✅ Simplicity: Standard libraries, well-documented patterns
- ✅ Performance: All queries <10ms for 1000 locations

---

## Next Steps

Phase 0 complete. Proceed to Phase 1:
1. Create data-model.md with concrete Pydantic models
2. Generate contract tests for Query/Mutations/Factory interfaces
3. Write quickstart.md with grid epidemic scenario
4. Update CLAUDE.md with new dependencies
