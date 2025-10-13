# Feature Specification: Complex Data Type Support for State Variables

**Feature Branch**: `014-data-variable-type`
**Created**: 2025-10-13
**Status**: Draft
**Input**: User description: "data-variable-type-expansion as described in FRAMEWORK_LIMITATION_ANALYSIS.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Dictionary Variables for Inventory Systems (Priority: P1)

A simulation developer needs to model trading agents with dynamic inventories where the list of goods is not known at configuration time or varies between agents. They define an inventory as a dictionary mapping good names to quantities.

**Why this priority**: This is the most fundamental limitation blocking real-world simulations. Without dictionary support, users cannot model any system with dynamic key-value collections (inventories, resource pools, attributes).

**Independent Test**: Can be fully tested by creating a YAML config with a dict-typed state variable, running initialization, and verifying the agent state contains the dictionary with correct types and values.

**Acceptance Scenarios**:

1. **Given** a YAML config with `inventory: {type: dict, key_type: str, value_type: float, default: {}}`, **When** simulation initializes, **Then** agents have an empty inventory dictionary that accepts string keys and float values
2. **Given** an agent with inventory `{food: 10.0, metal: 5.0}`, **When** simulation checkpoints, **Then** the inventory serializes to JSON and can be restored exactly
3. **Given** a config with fixed-schema dict `stats: {type: dict, schema: {health: {type: float, min: 0, max: 100}}}`, **When** simulation initializes with invalid values, **Then** validation fails with clear error indicating which field violated constraints

---

### User Story 2 - Define Tuple Variables for Spatial Coordinates (Priority: P1)

A simulation developer needs to track agent positions in 2D/3D space using coordinate tuples like `(x, y)` or `(x, y, z)`. They define location as a tuple with typed elements.

**Why this priority**: Equally critical as dictionaries - spatial simulations are a major use case and cannot be modeled without coordinate types. Independent of dictionary functionality.

**Independent Test**: Can be tested independently by creating a config with tuple-typed variables, verifying type enforcement per element, and testing immutability.

**Acceptance Scenarios**:

1. **Given** a YAML config with `location: {type: tuple, item_types: [float, float], default: [0.0, 0.0]}`, **When** simulation initializes, **Then** agents have location `(0.0, 0.0)` as a tuple
2. **Given** a config with per-element constraints `color: {type: tuple, item_types: [int, int, int], min: [0, 0, 0], max: [255, 255, 255]}`, **When** simulation initializes with value `[300, 100, 50]`, **Then** validation fails on first element exceeding max
3. **Given** an agent with location tuple, **When** code attempts to modify tuple in-place, **Then** operation fails maintaining immutability

---

### User Story 3 - Define List Variables for History Tracking (Priority: P2)

A simulation developer needs to track the last N actions taken by each agent as an ordered sequence. They define action history as a list with max length constraint.

**Why this priority**: Useful for logging and analysis but not blocking basic simulation functionality. Can be implemented after dict and tuple since it's less commonly needed for core simulation state.

**Independent Test**: Can be tested by creating configs with list-typed variables, adding items, verifying type checking, and testing length constraints.

**Acceptance Scenarios**:

1. **Given** a YAML config with `action_history: {type: list, item_type: str, max_length: 10, default: []}`, **When** simulation initializes, **Then** agents have an empty list that enforces string items and max 10 elements
2. **Given** an agent with history list at max_length (10 items), **When** 11th item is added, **Then** validation error is raised and addition is rejected with clear error message
3. **Given** a config with `position_history: {type: list, item_type: {type: tuple, item_types: [float, float]}}`, **When** simulation runs, **Then** list correctly stores tuples as items

---

### User Story 4 - Define Unrestricted String Variables (Priority: P2)

A simulation developer needs agents to reference dynamic locations or entities by name without enumerating all possible values upfront. They define a string variable with optional validation patterns.

**Why this priority**: Enables more flexible simulations but workarounds exist (using categorical with liberal values or storing as metadata). Important for usability but not blocking.

**Independent Test**: Can be tested by creating configs with unrestricted string variables, testing pattern validation, nullable behavior, and length constraints independently.

**Acceptance Scenarios**:

1. **Given** a YAML config with `target_destination: {type: str, default: null}`, **When** simulation initializes, **Then** agents can have null or any string value for destination
2. **Given** a config with `agent_name: {type: str, pattern: "^[A-Za-z ]+$", max_length: 50}`, **When** agent name set to "Agent123", **Then** validation fails due to pattern mismatch
3. **Given** a string variable with max_length constraint, **When** value exceeds length, **Then** validation fails with clear message indicating length violation

---

### User Story 5 - Define Nested Object Variables for Complex Entities (Priority: P3)

A simulation developer needs to model towns with multiple properties (position, inventory, prices, population). They define a global variable as a dict mapping town names to nested objects with schemas.

**Why this priority**: Most complex feature requiring dict, tuple, and nested validation. Should be implemented last after foundation types are solid. Valuable for advanced simulations but lower priority.

**Independent Test**: Can be tested by creating configs with deeply nested structures, verifying validation at all levels, and testing serialization of complex objects.

**Acceptance Scenarios**:

1. **Given** a YAML config with nested structure `towns: {type: dict, key_type: str, value_type: {type: object, schema: {position: {type: tuple, item_types: [float, float]}, inventory: {type: dict, key_type: str, value_type: float}}}}`, **When** simulation initializes, **Then** towns can be added with validated nested structure
2. **Given** a nested object with constraints at multiple levels, **When** validation fails on deeply nested field, **Then** error message clearly indicates path to failed field (e.g., "towns.Agriculture Town.inventory.food: expected float, got str")
3. **Given** a global state with nested town objects, **When** simulation checkpoints, **Then** entire nested structure serializes and deserializes correctly

---

### User Story 6 - Migrate Existing Scalar-Only Simulation (Priority: P1)

A developer with an existing simulation using only float, int, bool, and categorical types upgrades to the new version with complex type support. Their simulation continues to work without modification.

**Why this priority**: Backward compatibility is critical - existing users must not experience breakage. This is a requirement for all new functionality.

**Independent Test**: Can be tested by running the existing test suite for scalar-only simulations against the new version and verifying all tests pass with no code changes.

**Acceptance Scenarios**:

1. **Given** an existing YAML config using only scalar types (float, int, bool, categorical), **When** simulation runs on new version, **Then** simulation executes identically to previous version
2. **Given** existing checkpoints from scalar-only simulations, **When** loaded on new version, **Then** checkpoints restore correctly
3. **Given** performance benchmarks from scalar-only simulations, **When** re-run on new version, **Then** no performance regression detected (< 5% difference)

---

### Edge Cases

- Nesting depth limits: Config rejected at load time when dict exceeds 4 levels or list exceeds 3 levels (see FR-006a, FR-011a)
- Circular references: Detected and rejected at config load time with cycle path shown (see FR-024, FR-024a)
- Checkpoint schema mismatch: System fails load with clear error when checkpoint contains types not in current config (see FR-033-NEW)
- Collection size limits: Validation rejected when dict or list exceeds 1000 items (see FR-028a, FR-028b)
- What happens when a list's max_length is reduced in config after checkpoints contain longer lists?
- How does validation handle Unicode strings with emojis or special characters?
- What happens when tuple element types are changed in config after checkpoints exist?
- How does system handle None/null values in optional complex fields?

## Requirements *(mandatory)*

### Functional Requirements

**Dictionary Type Support:**

- **FR-001**: System MUST support dict type in VariableDefinition with configurable key and value types
- **FR-002**: System MUST support dict type with dynamic keys (key_type + value_type specification)
- **FR-003**: System MUST support dict type with fixed schema (predefined keys with individual type constraints)
- **FR-004**: System MUST validate dict keys match specified key_type (str, int)
- **FR-005**: System MUST validate dict values match specified value_type (any supported scalar or complex type)
- **FR-006**: System MUST support nested dicts (dict of dict) up to depth of 4 levels
- **FR-006a**: System MUST reject config at load time with clear error when dict nesting exceeds maximum depth of 4 levels

**List Type Support:**

- **FR-007**: System MUST support list type in VariableDefinition with configurable item type
- **FR-008**: System MUST validate all list items match specified item_type
- **FR-009**: System MUST support optional max_length constraint on lists
- **FR-010**: System MUST support lists of complex types (list of dict, list of tuple, list of object)
- **FR-011**: System MUST support nested lists (list of list) up to depth of 3 levels
- **FR-011a**: System MUST reject config at load time with clear error when list nesting exceeds maximum depth of 3 levels

**Tuple Type Support:**

- **FR-012**: System MUST support tuple type in VariableDefinition with typed elements
- **FR-013**: System MUST enforce fixed length matching number of item_types specified
- **FR-014**: System MUST validate each tuple element against corresponding item_type
- **FR-015**: System MUST support per-element constraints (min, max) on tuple elements
- **FR-016**: System MUST enforce tuple immutability (prevent in-place modification)

**String Type Support:**

- **FR-017**: System MUST support unrestricted str type without requiring value enumeration
- **FR-018**: System MUST support optional regex pattern validation for strings
- **FR-019**: System MUST support optional max_length constraint for strings
- **FR-020**: System MUST support nullable strings (default: null allowed)

**Nested Object Support:**

- **FR-021**: System MUST support object type with nested schema definition
- **FR-022**: System MUST validate nested objects recursively at all levels
- **FR-023**: System MUST support objects containing any combination of supported types
- **FR-024**: System MUST detect and reject circular references in object schemas at config load time (schema definition phase)
- **FR-024a**: System MUST provide clear error indicating cycle path when circular reference detected (e.g., "Circular reference: TypeA → TypeB → TypeA")

**Validation:**

- **FR-025**: System MUST validate complex types at simulation initialization
- **FR-026**: System MUST provide clear error messages indicating path to failed field (e.g., "agent_state.inventory.food")
- **FR-027**: System MUST validate complex types during checkpoint restoration
- **FR-028**: System MUST perform type validation in under 10ms for typical simulation states (< 100 agents, < 50 variables each)
- **FR-028a**: System MUST enforce maximum collection size of 1000 items per dict or list variable
- **FR-028b**: System MUST reject validation with clear error when any dict or list exceeds 1000 items

**Serialization:**

- **FR-029**: System MUST serialize all complex types to JSON for checkpointing
- **FR-030**: System MUST deserialize JSON checkpoints back to original complex types
- **FR-031**: System MUST preserve type constraints during deserialization
- **FR-032**: System MUST handle None/null values in optional complex fields
- **FR-033-NEW**: System MUST fail checkpoint load with clear schema mismatch error when checkpoint contains types not defined in current config schema

**Backward Compatibility:**

- **FR-034**: System MUST support all existing scalar types (float, int, bool, categorical) unchanged
- **FR-035**: System MUST run existing scalar-only simulation configs without modification
- **FR-036**: System MUST load checkpoints from previous versions with only scalar types
- **FR-037**: System MUST not introduce performance regression for scalar-only simulations

### Key Entities *(include if feature involves data)*

- **VariableDefinition**: Configuration schema for state variables, extended to support complex types (dict, list, tuple, str, object) with nested validation rules
- **AgentState**: Dynamic Pydantic model representing individual agent state, generated from VariableDefinition schemas including complex types
- **GlobalState**: Dynamic Pydantic model representing shared simulation state, generated from VariableDefinition schemas including complex types
- **Checkpoint**: Serialized snapshot of simulation state including complex nested structures, stored as JSON

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Trading simulation example (with inventory dict, location tuple, towns nested dict) successfully runs from YAML config to completion
- **SC-002**: Invalid complex type configurations are rejected at simulation initialization with error messages indicating exact field and violation
- **SC-003**: Simulation with 100 agents each having complex state (3 dicts, 2 lists, 1 tuple) completes validation in under 10 milliseconds
- **SC-004**: Complex state structures serialize to JSON checkpoint and deserialize back to identical state (round-trip equality verified)
- **SC-005**: All existing test suite tests for scalar-only simulations pass without modification on new version
- **SC-006**: Performance benchmarks for existing scalar-only simulations show less than 5% time difference compared to previous version
- **SC-007**: Documentation includes working examples for each new type (dict, list, tuple, str, object) with validation rules explained
- **SC-008**: Validation error for nested structure (e.g., towns.Agriculture Town.inventory.food) clearly indicates full path to failed field in error message

## Clarifications

### Session 2025-10-13

- Q: When a list with max_length constraint receives an item that would exceed the limit, should the system automatically remove the oldest item (FIFO) or raise a validation error? → A: Raise validation error and reject the addition
- Q: What happens when checkpoint contains a complex type that's no longer defined in updated config schema? → A: Fail checkpoint load with clear schema mismatch error
- Q: What happens when a dict/object exceeds the maximum nesting depth (4 levels for dict, 3 for list)? → A: Reject at config load time with clear depth limit error
- Q: How does system handle extremely large collections (e.g., 10,000 item inventory) during validation? → A: Hard limit of 1000 items maximum - reject larger collections
- Q: How does validation handle circular references in nested object schemas? → A: Detect and reject at schema definition time (config load)

## Assumptions

- Python's native dict, list, and tuple types provide sufficient performance for typical simulation scales (< 1000 agents, < 100 variables per agent)
- JSON serialization is acceptable for checkpoint format (no binary format needed for complex types)
- Maximum nesting depth of 4 levels is sufficient for practical simulation scenarios
- Validation overhead of < 10ms is acceptable given current scalar validation takes < 1ms
- Regex pattern validation for strings using Python's `re` module is sufficient
- Immutability for tuples follows Python semantics (tuple itself immutable, but contents may be mutable if complex types)
- Default behavior for list max_length violations is to raise validation error (not auto-truncate)
- Schema validation happens at initialization and checkpoint load, not on every state mutation during simulation
