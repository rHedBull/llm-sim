# Spatial Simulation Examples

Example configurations demonstrating spatial topology features (Feature 012-spatial-maps).

## Files

### Example Configurations

1. **epidemic_grid_config.yaml** (Task T042)
   - Grid-based epidemic simulation
   - 10x10 grid with 4-way connectivity
   - 5 agents tracking disease spread
   - Demonstrates: Grid topology, spatial movement validation, infection tracking

2. **geopolitics_config.yaml** (Task T043)
   - Multi-faction geopolitical simulation
   - GeoJSON topology with 7 regions (Westeros-inspired)
   - Houses compete for control and resources
   - Demonstrates: GeoJSON topology, location attributes, multi-layer networks

3. **supply_chain_config.yaml** (Task T044)
   - Supply chain optimization simulation
   - Network topology with 12 nodes, 14 edges
   - Multiple transport modes (road, rail, air)
   - Demonstrates: Network topology, multi-layer connectivity, connection attributes

### Data Files

4. **westeros.geojson** (Task T045)
   - 7 geographic regions with polygon geometries
   - Properties: loyalty, population, resources, military
   - Valid GeoJSON FeatureCollection format

5. **supply_network.json** (Task T046)
   - 12 nodes: factories, warehouses, distribution centers, retailers, suppliers
   - 14 edges: road, rail, air connections
   - Attributes: distance, time, cost, capacity

## Usage

Load and validate configurations:

```bash
# Test epidemic config
uv run python -c "from src.llm_sim.models.config import load_config; \
  config = load_config('examples/spatial/epidemic_grid_config.yaml'); \
  print(f'Loaded: {config.simulation.name}')"

# Test geopolitics config
uv run python -c "from src.llm_sim.models.config import load_config; \
  config = load_config('examples/spatial/geopolitics_config.yaml'); \
  print(f'Loaded: {config.simulation.name}')"

# Test supply chain config
uv run python -c "from src.llm_sim.models.config import load_config; \
  config = load_config('examples/spatial/supply_chain_config.yaml'); \
  print(f'Loaded: {config.simulation.name}')"
```

## Key Features Demonstrated

### Grid Topology
- Square grid with configurable size
- 4-way or 8-way connectivity
- Optional toroidal wrapping
- Cell coordinates as location IDs

### GeoJSON Topology
- Geographic regions from GeoJSON
- Polygon geometries with adjacency detection
- Rich location properties
- Multiple network layers (borders, trade, alliances)

### Network Topology
- Custom graph structure from JSON
- Multiple overlay networks
- Connection attributes (speed, cost, capacity)
- Heterogeneous node types

### Spatial Features
- Agent positioning at locations
- Location attributes (resources, terrain, etc.)
- Multi-layer network connectivity
- Spatial movement validation

## Next Steps

After implementing spatial features:
1. Run simulations: `uv run python -m llm_sim.main examples/spatial/epidemic_grid_config.yaml`
2. Verify checkpoints contain spatial state
3. Test spatial queries and mutations
4. Validate movement constraints
5. Implement remaining topology types (hex grid)
