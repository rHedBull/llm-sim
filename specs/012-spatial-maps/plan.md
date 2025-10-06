# Implementation Plan: Spatial Positioning and Topology

**Branch**: `012-spatial-maps` | **Date**: 2025-10-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-spatial-maps/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
   → Spec found at /specs/012-spatial-maps/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
   → Detect Project Type: single (Python library/framework)
   → Set Structure Decision: src/tests pattern
3. Fill Constitution Check section ✓
4. Evaluate Constitution Check section
   → No violations - aligns with all principles
   → Update Progress Tracking: Initial Constitution Check ✓
5. Execute Phase 0 → research.md
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check section
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
This feature adds optional spatial positioning and topology capabilities to the simulation framework, enabling agents to exist in various spatial topologies (grids, networks, geographic regions) with location-based interactions. The implementation maintains backward compatibility by making spatial features entirely optional through configuration. The architecture follows a state-first design with immutable spatial state, read-only query utilities for agents/validators, and write mutations restricted to engines only.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic 2.x (state models), PyYAML 6.x (config), structlog 24.x (logging), NetworkX (graph algorithms for shortest path)
**Storage**: File system (YAML configs, JSON checkpoints for spatial state persistence)
**Testing**: pytest (unit, integration, contract tests)
**Target Platform**: Linux/macOS/Windows (cross-platform Python)
**Project Type**: single (Python library/framework)
**Performance Goals**: Spatial queries O(1) for positions, O(E) for pathfinding, support 1000+ locations with <10ms query time
**Constraints**: Immutable state (Pydantic frozen models), backward compatible (spatial_state=None for existing sims), serializable for checkpoints
**Scale/Scope**: Support 4 topology types (grid, hex, network, geojson), 50+ locations, 100+ agents, multiple network layers

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: KISS (Keep It Simple and Stupid)
✅ **PASS** - Uses simple data structures (dicts, sets) for spatial state
✅ **PASS** - Static utility classes (SpatialQuery, SpatialMutations) avoid OOP complexity
✅ **PASS** - Factory pattern only for 4 topology types (justified by clear use cases)
✅ **PASS** - Configuration uses simple YAML schema extensions

### Principle 2: DRY (Don't Repeat Yourself)
✅ **PASS** - Single SpatialState model for all topology types
✅ **PASS** - Reusable query/mutation utilities across components
✅ **PASS** - Network abstraction eliminates topology-specific query code duplication
✅ **PASS** - Centralized factory for topology creation

### Principle 3: No Legacy Support
✅ **PASS** - No legacy compatibility layers
✅ **PASS** - Optional spatial_state field (None = feature not used, not legacy mode)
✅ **PASS** - Clean addition to existing state model without fallback logic

### Principle 4: Test-First Development
✅ **PASS** - Contract tests for query/mutation operations first
✅ **PASS** - Topology factory tests before implementation
✅ **PASS** - Integration tests with agents/engines before feature code
✅ **PASS** - Red-Green-Refactor cycle enforced

### Principle 5: Clean Interface Design
✅ **PASS** - Explicit type annotations on all query/mutation methods
✅ **PASS** - Single responsibility: queries read, mutations write
✅ **PASS** - Composable operations (e.g., filter_state_by_proximity composes with observability)
✅ **PASS** - Clear access control via separate Query/Mutations classes

### Principle 6: Observability and Debugging
✅ **PASS** - Structured logging for factory operations and state updates
✅ **PASS** - Clear validation errors with remediation steps for config issues
✅ **PASS** - Spatial state fully serializable for inspection
✅ **PASS** - Debug-friendly text-based configs (YAML/JSON)

### Principle 7: Python Package Management with uv
✅ **PASS** - All dependencies via `uv add` (NetworkX for graph algorithms)
✅ **PASS** - Tests run via `uv run pytest`
✅ **PASS** - pyproject.toml as single source of dependency truth

**Result**: All constitutional principles satisfied. No violations to track.

## Project Structure

### Documentation (this feature)
```
specs/012-spatial-maps/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── spatial_query_contract.py
│   ├── spatial_mutations_contract.py
│   └── spatial_factory_contract.py
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/llm_sim/
├── models/
│   ├── state.py          # Add: SpatialState, LocationState, NetworkState, ConnectionState
│   └── config.py         # Add: SpatialConfig, topology configs, update AgentConfig
│
├── infrastructure/
│   └── spatial/          # NEW MODULE
│       ├── __init__.py
│       ├── factory.py    # SpatialStateFactory + topology-specific factories
│       ├── query.py      # SpatialQuery (read-only utilities)
│       └── mutations.py  # SpatialMutations (write utilities)
│
├── orchestrator.py       # Update: initialize spatial_state, compose observations
│
└── infrastructure/base/
    ├── agent.py          # No changes (can use SpatialQuery via imports)
    ├── engine.py         # No changes (can use SpatialQuery + SpatialMutations)
    └── validator.py      # No changes (can use SpatialQuery)

tests/
├── contract/
│   ├── test_spatial_query_contract.py       # Query interface contracts
│   ├── test_spatial_mutations_contract.py   # Mutations interface contracts
│   └── test_spatial_factory_contract.py     # Factory interface contracts
│
├── unit/
│   ├── test_spatial_state_models.py         # Pydantic model tests
│   ├── test_spatial_config.py               # Config validation tests
│   ├── test_grid_factory.py                 # Grid topology factory
│   ├── test_hex_factory.py                  # Hex topology factory
│   ├── test_network_factory.py              # Network topology factory
│   ├── test_geojson_factory.py              # GeoJSON topology factory
│   ├── test_spatial_queries.py              # Query operations
│   ├── test_spatial_mutations.py            # Mutation operations
│   └── test_spatial_serialization.py        # Checkpoint persistence
│
└── integration/
    ├── test_spatial_agent_integration.py    # Agents using spatial queries
    ├── test_spatial_engine_integration.py   # Engines using mutations
    ├── test_spatial_validator_integration.py # Validators checking spatial legality
    ├── test_spatial_observability.py        # Proximity filtering + observability
    └── test_backward_compatibility_spatial.py # Spatial=None backward compat
```

**Structure Decision**: Single project structure selected. This is a library/framework project with a clear src/tests division. The spatial module fits cleanly into the existing `infrastructure/` pattern alongside `lifecycle/`, `observability/`, and `events/`. All new spatial code is isolated in the `infrastructure/spatial/` directory with minimal changes to existing files (only models, config, and orchestrator need updates).

## Phase 0: Outline & Research

### Unknowns to Research
1. **NetworkX integration**: Best practices for integrating NetworkX for shortest path algorithms while maintaining immutability
2. **GeoJSON parsing**: Best library/approach for parsing GeoJSON and computing polygon adjacency
3. **Hex grid coordinates**: Standard coordinate system for hexagonal grids (axial vs cube coordinates)
4. **Serialization strategy**: How to serialize NetworkX-like graph structures in Pydantic models

### Research Tasks
Generating research.md with decisions on:
- **Decision 1**: NetworkX usage pattern (wrap in pure functions vs. build custom graph)
- **Decision 2**: GeoJSON library choice (shapely vs. geojson library)
- **Decision 3**: Hex coordinate system (axial recommended for simplicity)
- **Decision 4**: Graph serialization (edge list format for JSON compatibility)

**Output**: research.md

## Phase 1: Design & Contracts

### Data Model (data-model.md)
Extract entities from spec and architecture doc:

**Entity: SpatialState**
- Fields: topology_type, agent_positions, locations, connections, networks
- Validation: topology_type must match available factories
- Immutability: Pydantic frozen=True

**Entity: LocationState**
- Fields: id, attributes (Dict), metadata (Dict)
- Validation: id must be non-empty string

**Entity: NetworkState**
- Fields: name, edges (Set[Tuple[str, str]]), attributes (Dict)
- Validation: edge tuples must reference valid location IDs

**Entity: ConnectionState**
- Fields: type, attributes (Dict), bidirectional (bool)
- Validation: attributes can be arbitrary JSON-serializable values

**Entity: SpatialConfig**
- Fields: type (Literal["grid", "hex_grid", "network", "geojson"]), type-specific fields
- Validation: type determines which topology-specific fields are required

### API Contracts (contracts/)

**Contract 1: SpatialQuery Interface**
```python
# test_spatial_query_contract.py
def test_get_agent_position_returns_optional_str():
    """SpatialQuery.get_agent_position must return Optional[str]"""

def test_get_neighbors_returns_list_str():
    """SpatialQuery.get_neighbors must return List[str]"""

def test_get_distance_returns_int():
    """SpatialQuery.get_distance must return int (hops)"""

# ... additional contract tests for all 15 query methods
```

**Contract 2: SpatialMutations Interface**
```python
# test_spatial_mutations_contract.py
def test_move_agent_returns_spatial_state():
    """SpatialMutations.move_agent must return new SpatialState"""

def test_move_agent_preserves_immutability():
    """SpatialMutations.move_agent must not modify input state"""

# ... additional contract tests for all 10 mutation methods
```

**Contract 3: SpatialStateFactory Interface**
```python
# test_spatial_factory_contract.py
def test_create_dispatches_by_type():
    """SpatialStateFactory.create must dispatch to correct factory"""

def test_from_grid_config_returns_spatial_state():
    """Factory must return valid SpatialState for grid topology"""

# ... contract tests for each topology type factory
```

### Quickstart Test Scenario (quickstart.md)
**Scenario**: Grid-based epidemic simulation
1. Configure 10×10 grid with agents at random positions
2. Agent queries neighbors within radius 1
3. Engine moves infected agents
4. Validator checks moves are to adjacent cells
5. Verify spatial state persists to checkpoint

### Agent Context Update
Execute: `.specify/scripts/bash/update-agent-context.sh claude`
- Add: Python 3.12 + Pydantic 2.x, NetworkX, shapely (if GeoJSON)
- Add: File system (JSON checkpoints with spatial state)
- Update recent changes: 012-spatial-maps

**Output**: data-model.md, contracts/, quickstart.md, CLAUDE.md (updated)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design:
   - Contract test tasks (15+ tests) [P]
   - Model creation tasks (4 entities) [P]
   - Factory implementation tasks (4 topology types)
   - Query utilities task (15 methods)
   - Mutation utilities task (10 methods)
   - Orchestrator integration task
   - Integration test tasks (5 scenarios)
   - Backward compatibility test task
   - Example configuration tasks (3 examples)

**Ordering Strategy**:
1. **Phase 1: Models & Contracts** [P = parallel within phase]
   - Task 1: Write contract tests for SpatialQuery [P]
   - Task 2: Write contract tests for SpatialMutations [P]
   - Task 3: Write contract tests for SpatialStateFactory [P]
   - Task 4: Implement SpatialState, LocationState, NetworkState, ConnectionState models [P]
   - Task 5: Implement SpatialConfig models [P]

2. **Phase 2: Factory Implementation**
   - Task 6: Implement SpatialStateFactory.from_grid_config()
   - Task 7: Implement SpatialStateFactory.from_hex_config()
   - Task 8: Implement SpatialStateFactory.from_network_config()
   - Task 9: Implement SpatialStateFactory.from_geojson()

3. **Phase 3: Query & Mutation Utilities**
   - Task 10: Implement SpatialQuery navigation methods (get_neighbors, get_distance, etc.)
   - Task 11: Implement SpatialQuery agent methods (get_agent_position, get_agents_at, etc.)
   - Task 12: Implement SpatialQuery location methods (get_location_attribute, etc.)
   - Task 13: Implement SpatialMutations agent methods (move_agent, move_agents_batch)
   - Task 14: Implement SpatialMutations location methods (set_location_attribute, etc.)
   - Task 15: Implement SpatialMutations network methods (add_connection, create_network, etc.)

4. **Phase 4: Integration**
   - Task 16: Update SimulationState model with spatial_state field
   - Task 17: Update AgentConfig with initial_location field
   - Task 18: Integrate spatial_state initialization in orchestrator
   - Task 19: Implement spatial proximity filtering
   - Task 20: Compose spatial + observability filtering

5. **Phase 5: Testing & Examples**
   - Task 21: Write integration tests for agent spatial queries
   - Task 22: Write integration tests for engine spatial mutations
   - Task 23: Write integration tests for validator spatial checks
   - Task 24: Write backward compatibility tests (spatial_state=None)
   - Task 25: Create grid epidemic example config
   - Task 26: Create GeoJSON geopolitics example config
   - Task 27: Create multi-layer network example config
   - Task 28: Update documentation with spatial features overview

**Estimated Output**: 28 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)
**Phase 5**: Validation (run all tests, execute quickstart.md, verify examples work)

## Complexity Tracking
*No complexity violations - table not needed*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md created
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, CLAUDE.md created
- [x] Phase 2: Task planning complete (/plan command - approach described above)
- [x] Phase 3: Tasks generated (/tasks command) - tasks.md with 55 ordered tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

**Artifacts Generated**:
- ✅ research.md - Technology decisions (NetworkX, shapely, axial hex coords, edge list serialization)
- ✅ data-model.md - 12 Pydantic models with full field definitions
- ✅ contracts/spatial_query_contract.md - 12 query method contracts
- ✅ contracts/spatial_mutations_contract.md - 10 mutation method contracts
- ✅ contracts/spatial_factory_contract.md - 5 factory method contracts
- ✅ quickstart.md - Grid epidemic simulation test scenario
- ✅ CLAUDE.md - Updated with NetworkX, shapely dependencies

---
*Based on Constitution v1.3.0 - See `.specify/memory/constitution.md`*
