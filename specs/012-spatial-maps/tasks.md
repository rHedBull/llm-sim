# Tasks: Spatial Positioning and Topology

**Input**: Design documents from `/specs/012-spatial-maps/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.12, Pydantic 2.x, NetworkX, shapely, geojson
   → Structure: Single project (src/tests)
2. Load optional design documents ✓
   → data-model.md: 12 entities (4 core, 4 topology configs, 4 extensions)
   → contracts/: 3 contract files (query, mutations, factory)
   → research.md: 4 technology decisions
   → quickstart.md: Grid epidemic test scenario
3. Generate tasks by category ✓
4. Apply task rules ✓
   → Different files = [P]
   → Tests before implementation (TDD)
5. Number tasks sequentially ✓
6. Generate dependency graph ✓
7. Create parallel execution examples ✓
8. Validate task completeness ✓
9. SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup & Dependencies

- [X] **T001** Add NetworkX dependency via `uv add networkx`
- [X] **T002** Add shapely dependency via `uv add shapely` (for GeoJSON support)
- [X] **T003** Add geojson dependency via `uv add geojson` (for GeoJSON parsing)
- [X] **T004** Create `src/llm_sim/infrastructure/spatial/` directory structure with `__init__.py`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests [P] - All can run in parallel
- [ ] **T005** [P] Write contract tests for SpatialQuery interface in `tests/contract/test_spatial_query_contract.py`
  - Test all 12 query methods (get_agent_position, get_neighbors, get_distance, is_adjacent, shortest_path, get_agents_at, get_agents_within, get_location_attribute, get_locations_by_attribute, has_connection, get_connection_attribute, filter_state_by_proximity)
  - Verify return types, None handling, edge cases
  - Verify immutability (no input mutation)

- [ ] **T006** [P] Write contract tests for SpatialMutations interface in `tests/contract/test_spatial_mutations_contract.py`
  - Test all 10 mutation methods (move_agent, move_agents_batch, set_location_attribute, update_location_attributes, add_connection, remove_connection, update_connection_attribute, create_network, remove_network, apply_to_region)
  - Verify returns new SpatialState, immutability, validation errors

- [ ] **T007** [P] Write contract tests for SpatialStateFactory interface in `tests/contract/test_spatial_factory_contract.py`
  - Test factory dispatcher (create method)
  - Test all 4 topology factories (grid, hex, network, geojson)
  - Verify location_attributes application, additional_networks creation

### Unit Tests for Models [P] - All can run in parallel
- [ ] **T008** [P] Write unit tests for spatial state models in `tests/unit/test_spatial_state_models.py`
  - Test LocationState, ConnectionState, NetworkState, SpatialState
  - Test Pydantic validation, frozen models, serialization

- [ ] **T009** [P] Write unit tests for spatial config models in `tests/unit/test_spatial_config.py`
  - Test GridConfig, HexGridConfig, NetworkConfig, GeoJSONConfig, SpatialConfig
  - Test validation, discriminated unions, file path checks

### Factory Unit Tests [P] - All can run in parallel
- [ ] **T010** [P] Write unit tests for grid factory in `tests/unit/test_grid_factory.py`
  - Test grid creation (width×height locations)
  - Test 4-connectivity vs 8-connectivity
  - Test wrapping (toroidal) vs bounded
  - Test neighbor calculations

- [ ] **T011** [P] Write unit tests for hex factory in `tests/unit/test_hex_factory.py`
  - Test hexagonal grid creation with radius
  - Test axial coordinate neighbors (6-connectivity)
  - Test coordinate format "{q},{r}"

- [ ] **T012** [P] Write unit tests for network factory in `tests/unit/test_network_factory.py`
  - Test loading from JSON edge list file
  - Test node and edge creation
  - Test file not found / malformed JSON errors

- [ ] **T013** [P] Write unit tests for GeoJSON factory in `tests/unit/test_geojson_factory.py`
  - Test loading from GeoJSON file
  - Test polygon adjacency computation
  - Test feature properties to location attributes mapping

### Query/Mutation Unit Tests [P] - All can run in parallel
- [ ] **T014** [P] Write unit tests for spatial queries in `tests/unit/test_spatial_queries.py`
  - Test navigation queries (neighbors, distance, adjacency, shortest_path)
  - Test agent queries (position, agents_at, agents_within)
  - Test location queries (get_attribute, filter by attribute)
  - Test None spatial_state handling

- [ ] **T015** [P] Write unit tests for spatial mutations in `tests/unit/test_spatial_mutations.py`
  - Test agent movement (single and batch)
  - Test location attribute updates
  - Test network/connection modifications
  - Test immutability preservation

- [ ] **T016** [P] Write unit tests for spatial serialization in `tests/unit/test_spatial_serialization.py`
  - Test SpatialState JSON serialization
  - Test edge list serialization/deserialization
  - Test checkpoint persistence round-trip

### Integration Tests [P] - All can run in parallel
- [ ] **T017** [P] Write integration test for agents using spatial queries in `tests/integration/test_spatial_agent_integration.py`
  - Test agent querying position and neighbors
  - Test agent observing nearby agents
  - Test spatial context in LLM agent prompts

- [ ] **T018** [P] Write integration test for engines using mutations in `tests/integration/test_spatial_engine_integration.py`
  - Test engine moving agents
  - Test engine updating location attributes
  - Test engine modifying networks

- [ ] **T019** [P] Write integration test for validators using spatial checks in `tests/integration/test_spatial_validator_integration.py`
  - Test validator checking move adjacency
  - Test validator rejecting invalid spatial actions
  - Test spatial constraint enforcement

- [ ] **T020** [P] Write integration test for spatial observability in `tests/integration/test_spatial_observability.py`
  - Test proximity-based filtering (filter_state_by_proximity)
  - Test composition with existing observability filtering
  - Test radius configuration

- [ ] **T021** [P] Write backward compatibility test in `tests/integration/test_backward_compatibility_spatial.py`
  - Test simulation runs with spatial_state=None
  - Test configs without spatial field work unchanged
  - Test checkpoint load/save with missing spatial_state

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### State Models [P] - Can run in parallel
- [ ] **T022** [P] Implement LocationState, ConnectionState, NetworkState in `src/llm_sim/models/state.py`
  - Add Pydantic models with frozen=True
  - Add field validators
  - Add field serializers for JSON compatibility

- [ ] **T023** [P] Implement SpatialState in `src/llm_sim/models/state.py`
  - Add Pydantic model with topology_type, agent_positions, locations, connections, networks
  - Add model validator for reference integrity
  - Add field serializers for connections dict

- [ ] **T024** Update SimulationState in `src/llm_sim/models/state.py`
  - Add spatial_state: Optional[SpatialState] field
  - Add field serializer for spatial_state

### Config Models [P] - Can run in parallel
- [ ] **T025** [P] Implement topology config models in `src/llm_sim/models/config.py`
  - Add GridConfig, HexGridConfig, NetworkConfig, GeoJSONConfig
  - Add file path validators
  - Add discriminated union SpatialConfig

- [ ] **T026** Update AgentConfig in `src/llm_sim/models/config.py`
  - Add initial_location: Optional[str] field

- [ ] **T027** Update SimulationConfig in `src/llm_sim/models/config.py`
  - Add spatial: Optional[SpatialConfig] field
  - Add validator for agent initial_location references

### Factory Implementation
- [ ] **T028** Implement SpatialStateFactory.from_grid_config in `src/llm_sim/infrastructure/spatial/factory.py`
  - Create width×height grid locations
  - Build adjacency network (4 or 8 connectivity)
  - Handle wrapping (toroidal grid)
  - Return SpatialState with topology_type="grid"

- [ ] **T029** Implement SpatialStateFactory.from_hex_config in `src/llm_sim/infrastructure/spatial/factory.py`
  - Create hexagonal grid using axial coordinates
  - Build 6-neighbor adjacency
  - Return SpatialState with topology_type="hex_grid"

- [ ] **T030** Implement SpatialStateFactory.from_network_config in `src/llm_sim/infrastructure/spatial/factory.py`
  - Load JSON file with nodes and edges
  - Create locations from nodes
  - Create network from edges
  - Return SpatialState with topology_type="network"

- [ ] **T031** Implement SpatialStateFactory.from_geojson in `src/llm_sim/infrastructure/spatial/factory.py`
  - Load GeoJSON file
  - Parse features and create locations
  - Compute polygon adjacency using shapely
  - Map properties to location attributes
  - Return SpatialState with topology_type="regions"

- [ ] **T032** Implement SpatialStateFactory.create dispatcher in `src/llm_sim/infrastructure/spatial/factory.py`
  - Dispatch to correct factory based on config.topology.type
  - Apply location_attributes from config
  - Create additional_networks from config
  - Return complete SpatialState

### Query Implementation
- [ ] **T033** Implement SpatialQuery navigation methods in `src/llm_sim/infrastructure/spatial/query.py`
  - Implement get_neighbors, get_distance, is_adjacent, shortest_path
  - Use NetworkX for shortest_path computation
  - Handle None spatial_state gracefully

- [ ] **T034** Implement SpatialQuery agent methods in `src/llm_sim/infrastructure/spatial/query.py`
  - Implement get_agent_position, get_agents_at, get_agents_within
  - Use distance calculations for radius queries

- [ ] **T035** Implement SpatialQuery location methods in `src/llm_sim/infrastructure/spatial/query.py`
  - Implement get_location_attribute, get_locations_by_attribute
  - Implement has_connection, get_connection_attribute

- [ ] **T036** Implement SpatialQuery.filter_state_by_proximity in `src/llm_sim/infrastructure/spatial/query.py`
  - Filter agents by proximity radius
  - Filter locations by proximity radius
  - Preserve global_state and other fields
  - Use immutable updates (model_copy)

### Mutation Implementation
- [ ] **T037** Implement SpatialMutations agent methods in `src/llm_sim/infrastructure/spatial/mutations.py`
  - Implement move_agent, move_agents_batch
  - Validate target locations exist
  - Return new SpatialState instances

- [ ] **T038** Implement SpatialMutations location methods in `src/llm_sim/infrastructure/spatial/mutations.py`
  - Implement set_location_attribute, update_location_attributes
  - Validate locations exist
  - Preserve immutability

- [ ] **T039** Implement SpatialMutations network methods in `src/llm_sim/infrastructure/spatial/mutations.py`
  - Implement add_connection, remove_connection, update_connection_attribute
  - Implement create_network, remove_network
  - Implement apply_to_region for batch updates

## Phase 3.4: Integration with Orchestrator

- [ ] **T040** Initialize spatial_state in orchestrator in `src/llm_sim/orchestrator.py`
  - Import SpatialStateFactory
  - Create spatial_state from config.spatial if present
  - Place agents at initial_location using SpatialMutations.move_agent
  - Pass spatial_state to initial SimulationState

- [ ] **T041** Implement spatial proximity filtering in observation construction in `src/llm_sim/orchestrator.py`
  - Add spatial filtering step before observability filtering
  - Use SpatialQuery.filter_state_by_proximity
  - Compose with existing observability system
  - Make radius configurable

## Phase 3.5: Examples & Documentation

- [ ] **T042** [P] Create grid epidemic example config in `examples/spatial/epidemic_grid_config.yaml`
  - 10×10 grid topology
  - 5 agents at initial positions
  - Spatial movement validator
  - Follow quickstart.md scenario

- [ ] **T043** [P] Create GeoJSON geopolitics example config in `examples/spatial/geopolitics_config.yaml`
  - GeoJSON topology from sample file
  - Multi-agent geopolitical simulation
  - Location attributes (loyalty, resources, military)
  - Multiple network layers (borders, trade routes)

- [ ] **T044** [P] Create multi-layer network example config in `examples/spatial/supply_chain_config.yaml`
  - Network topology from JSON
  - Multiple overlay networks (road, rail, air)
  - Connection attributes (speed, capacity, cost)
  - Supply chain optimization scenario

- [ ] **T045** [P] Create sample GeoJSON file in `examples/spatial/westeros.geojson`
  - Feature collection with 5-7 regions
  - Polygon geometries with adjacency
  - Properties: name, loyalty, population, resources

- [ ] **T046** [P] Create sample network JSON file in `examples/spatial/supply_network.json`
  - Nodes list with 10-15 locations
  - Edges list with connections
  - Attributes for nodes and edges

## Phase 3.6: Polish & Validation

- [ ] **T047** Run all contract tests and verify they pass
  - `uv run pytest tests/contract/test_spatial_*.py -v`
  - All 3 contract test files must pass

- [ ] **T048** Run all unit tests and verify they pass
  - `uv run pytest tests/unit/test_spatial_*.py -v`
  - All 9 unit test files must pass

- [ ] **T049** Run all integration tests and verify they pass
  - `uv run pytest tests/integration/test_spatial_*.py -v`
  - All 5 integration test files must pass

- [ ] **T050** Execute quickstart validation scenario
  - Follow `specs/012-spatial-maps/quickstart.md` step-by-step
  - All 8 steps must complete successfully
  - Grid epidemic simulation must run

- [ ] **T051** Run example simulations
  - Run epidemic_grid_config.yaml
  - Run geopolitics_config.yaml
  - Run supply_chain_config.yaml
  - Verify all complete without errors

- [ ] **T052** Performance validation
  - Test spatial queries with 1000 locations
  - Verify get_neighbors < 1ms
  - Verify shortest_path < 10ms for 1000 locations
  - Verify filter_state_by_proximity < 50ms for 100 agents

- [ ] **T053** [P] Update main README.md with spatial features section
  - Add overview of spatial capabilities
  - Add quick example
  - Link to examples/spatial/

- [ ] **T054** [P] Add docstrings to all public spatial methods
  - Add comprehensive docstrings to SpatialQuery methods
  - Add comprehensive docstrings to SpatialMutations methods
  - Add comprehensive docstrings to SpatialStateFactory methods

- [ ] **T055** Code quality check
  - Run `uv run ruff check src/llm_sim/infrastructure/spatial/`
  - Run `uv run mypy src/llm_sim/infrastructure/spatial/`
  - Fix any linting or type errors

## Dependencies

### Critical Paths
1. **Setup** (T001-T004) blocks everything
2. **Tests** (T005-T021) must complete and FAIL before implementation
3. **State Models** (T022-T024) block factory, query, mutations
4. **Config Models** (T025-T027) block factory and orchestrator
5. **Factory** (T028-T032) blocks integration tests
6. **Query** (T033-T036) blocks agent/validator integration
7. **Mutations** (T037-T039) blocks engine integration
8. **Orchestrator** (T040-T041) blocks example execution
9. **Examples** (T042-T046) block validation
10. **Polish** (T047-T055) comes last

### Detailed Dependencies
```
T001, T002, T003, T004 (setup)
  ↓
T005, T006, T007 (contract tests) [P]
T008, T009 (model tests) [P]
T010, T011, T012, T013 (factory tests) [P]
T014, T015, T016 (query/mutation tests) [P]
T017, T018, T019, T020, T021 (integration tests) [P]
  ↓ (tests must fail)
T022, T023 (state models) [P]
T025 (config models) [P]
  ↓
T024 (update SimulationState)
T026, T027 (update configs)
  ↓
T028, T029, T030, T031, T032 (factory implementation)
T033, T034, T035, T036 (query implementation)
T037, T038, T039 (mutation implementation)
  ↓
T040, T041 (orchestrator integration)
  ↓
T042, T043, T044, T045, T046 (examples) [P]
  ↓
T047, T048, T049 (test validation)
T050, T051 (scenario validation)
T052 (performance validation)
T053, T054, T055 (polish) [P]
```

## Parallel Execution Examples

### Phase 3.2: All Contract Tests Together
```bash
# Launch T005-T007 in parallel (3 different test files):
uv run pytest tests/contract/test_spatial_query_contract.py &
uv run pytest tests/contract/test_spatial_mutations_contract.py &
uv run pytest tests/contract/test_spatial_factory_contract.py &
wait
```

### Phase 3.2: All Unit Tests Together
```bash
# Launch T008-T016 in parallel (9 different test files):
uv run pytest tests/unit/test_spatial_state_models.py &
uv run pytest tests/unit/test_spatial_config.py &
uv run pytest tests/unit/test_grid_factory.py &
uv run pytest tests/unit/test_hex_factory.py &
uv run pytest tests/unit/test_network_factory.py &
uv run pytest tests/unit/test_geojson_factory.py &
uv run pytest tests/unit/test_spatial_queries.py &
uv run pytest tests/unit/test_spatial_mutations.py &
uv run pytest tests/unit/test_spatial_serialization.py &
wait
```

### Phase 3.2: All Integration Tests Together
```bash
# Launch T017-T021 in parallel (5 different test files):
uv run pytest tests/integration/test_spatial_agent_integration.py &
uv run pytest tests/integration/test_spatial_engine_integration.py &
uv run pytest tests/integration/test_spatial_validator_integration.py &
uv run pytest tests/integration/test_spatial_observability.py &
uv run pytest tests/integration/test_backward_compatibility_spatial.py &
wait
```

### Phase 3.3: State Models in Parallel
Tasks T022 and T025 can run in parallel (different sections of files):
- T022: Add LocationState, ConnectionState, NetworkState to state.py
- T025: Add GridConfig, HexGridConfig, etc. to config.py

### Phase 3.5: All Examples in Parallel
```bash
# Create T042-T046 in parallel (5 different files):
# All are independent file creation tasks
```

## Notes

- **[P] = Parallelizable**: Tasks marked [P] can run simultaneously because they modify different files
- **TDD Critical**: Tests T005-T021 MUST be written and failing before implementation T022-T041
- **Immutability**: All spatial state updates must use Pydantic model_copy, never mutate in place
- **Error Messages**: Include what failed, expected vs actual, valid alternatives, remediation steps
- **Commit Strategy**: Commit after each completed task with descriptive message

## Validation Checklist
*GATE: Verify before marking complete*

- [x] All contracts have corresponding tests (3 contracts → T005-T007)
- [x] All entities have model tasks (12 entities → T022-T027)
- [x] All tests come before implementation (T005-T021 before T022-T041)
- [x] Parallel tasks truly independent (different files verified)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Total: 55 tasks covering all requirements

## Task Summary by Phase

- **Setup (4 tasks)**: T001-T004
- **Tests (17 tasks)**: T005-T021
- **Models (6 tasks)**: T022-T027
- **Factory (5 tasks)**: T028-T032
- **Query/Mutations (7 tasks)**: T033-T039
- **Integration (2 tasks)**: T040-T041
- **Examples (5 tasks)**: T042-T046
- **Polish (9 tasks)**: T047-T055

**Total: 55 tasks** covering all 50 functional requirements plus setup, testing, examples, and polish.
