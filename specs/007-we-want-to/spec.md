# Feature Specification: Abstract Agent and Global State System

**Feature Branch**: `007-we-want-to`
**Created**: 2025-10-01
**Status**: Draft
**Input**: User description: "we want to make the Agent and global state more abstract to make the usage of the simulation loop more flexible. right now variables like economic_strenght inflation and so on are hardcoded. in the future we want to have enable GlobalState and AgentState to allow multiple variables and types to be tracked. this will be initally be defined in the simulation setup yaml. so one econ simulation track gdp, population per agent and world inflation float, open_economy boolean and another military simulation tracks technolocy level from a category, owned_regions int per agent and world_peace boolean, total casualty int.     these variable are defined with their type and min max, in the simulation setup config. since they are therefore also part of the Simulation state each turn they get saved in the checkpoint data"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

## Clarifications

### Session 2025-10-01
- Q: How should initial/default values for custom variables be specified when a simulation starts? → A: Defined in YAML config per variable (e.g., `gdp: {type: float, default: 1000.0}`)
- Q: Should min/max constraints be automatically enforced during simulation execution? → A: Yes, enforce automatically in the engine (reject/clamp values outside bounds)
- Q: How should categorical variables and their allowed values be defined in the YAML config? → A: Simple list (e.g., `tech_level: {type: categorical, values: [bronze, iron, steel]}`)
- Q: What should happen when a checkpoint is loaded but the variable definitions have changed since it was saved? → A: Reject load with error (strict schema compatibility required)
- Q: What should happen when an invalid variable type (unsupported type) is specified in the config? → A: Fail fast at config load time (validation error before simulation starts)

---

### Primary User Story
A simulation designer wants to create different types of simulations (economic, military, etc.) using the same simulation framework. They define custom state variables for both individual agents and the global environment in a configuration file, specifying the variable names, types, valid ranges, and default initial values. The simulation then tracks these custom variables throughout execution and persists them in checkpoint files.

### Acceptance Scenarios
1. **Given** a simulation setup config with agent variables (gdp: float, population: int), **When** the simulation initializes, **Then** each agent state tracks these custom variables with their specified types
7. **Given** a simulation config with an unsupported variable type (e.g., `score: {type: complex_number}`), **When** loading the configuration, **Then** the system fails with a validation error listing supported types
2. **Given** a simulation setup config with global variables (world_inflation: float, open_economy: boolean), **When** the simulation executes, **Then** the global state tracks these custom variables
6. **Given** a checkpoint file saved with variable schema X, **When** attempting to load with a different variable schema Y, **Then** the system rejects the load operation with a schema compatibility error
3. **Given** a running simulation with custom state variables, **When** a checkpoint is created, **Then** all custom agent and global variables are persisted in the checkpoint data
4. **Given** an economic simulation config and a military simulation config with different variables, **When** each simulation runs, **Then** each tracks only its configured variables without hardcoded assumptions
5. **Given** a variable definition with min/max constraints, **When** the simulation processes variable updates that exceed bounds, **Then** the system automatically enforces constraints (rejects or clamps the value)

### Edge Cases
- What happens when attempting to update a variable to a value that violates type constraints (e.g., setting a boolean to "maybe")?
- What happens when a default value in the config violates its own min/max constraints?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST allow simulation configurations to define custom agent state variables with name, type, and optional min/max constraints
- **FR-002**: System MUST allow simulation configurations to define custom global state variables with name, type, and optional min/max constraints
- **FR-003**: System MUST support multiple variable types including: float (decimal numbers), int (integers), boolean (true/false), and categorical (enumerated values)
- **FR-003a**: System MUST validate variable type specifications at configuration load time and reject configs with unsupported types before simulation initialization
- **FR-004**: System MUST initialize agent states with all configured custom variables at simulation start
- **FR-005**: System MUST initialize global state with all configured custom variables at simulation start
- **FR-006**: System MUST persist all custom agent and global variables in checkpoint data when saving simulation state
- **FR-007**: System MUST restore all custom agent and global variables from checkpoint data when loading simulation state
- **FR-007a**: System MUST validate that checkpoint variable schema matches current simulation configuration and reject load with error if schemas are incompatible
- **FR-008**: System MUST allow different simulations to use completely different sets of state variables without code changes
- **FR-009**: System MUST remove hardcoded assumptions about specific variables like "economic_strength" or "inflation"
- **FR-010**: Variable definitions MUST be specified in the simulation setup YAML configuration file
- **FR-011**: System MUST allow variable definitions to specify default/initial values in the YAML configuration (e.g., `gdp: {type: float, min: 0, max: 10000, default: 1000.0}`)
- **FR-012**: System MUST automatically enforce min/max constraints when variable values are updated during simulation execution (reject or clamp out-of-bounds values)
- **FR-013**: System MUST allow categorical variables to be defined with a simple list of allowed string values (e.g., `tech_level: {type: categorical, values: [bronze, iron, steel], default: bronze}`)
- **FR-014**: System MUST validate categorical variable assignments against the defined allowed values list and reject invalid values

### Key Entities *(include if feature involves data)*
- **AgentState**: Represents the state of an individual simulation agent. Contains dynamically configured variables based on simulation setup (e.g., gdp, population, technology_level, owned_regions). Variable set is defined per simulation type, not hardcoded.
- **GlobalState**: Represents world-level or simulation-wide state. Contains dynamically configured variables based on simulation setup (e.g., world_inflation, open_economy, world_peace, total_casualty). Variable set is defined per simulation type, not hardcoded.
- **VariableDefinition**: Describes a single state variable in the configuration. Specifies: variable name, data type (float/int/boolean/categorical), optional min/max constraints (for numeric types), allowed values list (for categorical type), and default initial value.
- **SimulationState**: The complete state of a simulation at a point in time. Contains the GlobalState and all AgentStates. Must be serializable to checkpoint files with all custom variables preserved.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---
