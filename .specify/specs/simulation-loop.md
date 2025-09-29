# Feature Specification: Simulation Loop

## Constitution Alignment
- **KISS Compliance**: Simple YAML-driven configuration with minimal components (Engine, Agent, Validator, State, Action) following clear single-responsibility patterns
- **DRY Compliance**: Standardized base classes for Agent, Validator, and Action ensure code reuse; centralized state management in Engine avoids duplication
- **No Legacy Support**: Clean greenfield implementation with no backwards compatibility concerns
- **Test-First Development**: Each component (Agent, Validator, Engine) will have unit tests; integration tests for the full simulation loop
- **Clean Interface Design**: Clear, explicit interfaces between components using typed dataclasses for State and Action
- **Observability**: Built-in logging at each simulation step; state snapshots available for debugging

## Scope

### What's Included
- YAML-based simulation configuration loader
- Core simulation engine with state management
- Standardized Agent base class with simple action selection
- Action validation system with Validator base class
- State and Action dataclasses with validation marking
- Economic simulation with interest-based growth
- Turn-based simulation loop with configurable limits
- Simple logging system for simulation events

### What's Excluded
- Persistence layer (states only in memory for MVP)
- Complex agent decision-making (agents use fixed strategies)
- Multi-threading or parallel processing
- Advanced economic models beyond simple interest
- Visualization or UI components
- Network communication between agents

## Requirements

### Functional Requirements
1. Load simulation configuration from YAML file defining initial state and parameters
2. Initialize simulation with N agents (MVP: 2 nations) each with economic_strength value
3. Execute turn-based simulation loop where:
   - Engine broadcasts current state to all agents
   - Each agent returns exactly one action
   - Validator validates all actions
   - Engine applies validated actions to update state
4. Apply economic growth each turn using configurable interest rate
5. Terminate simulation on max_turns or when values reach min/max thresholds
6. Log all simulation events and state changes

### Non-Functional Requirements
- **Simplicity**: Solution understandable by junior developers; no complex abstractions
- **Maintainability**: Clear separation of concerns; no duplicated state management logic
- **Testability**: Each component testable in isolation; minimal mocking required
- **Extensibility**: Easy to add new agent types or validation rules without modifying core

## Design Constraints

### Mandatory Simplicity Rules
- Maximum function complexity: Cyclomatic complexity ≤ 5
- Maximum class hierarchy depth: 3 levels (Base -> Concrete -> Specialized)
- Maximum file length: 200 lines
- Maximum function length: 30 lines

### Mandatory Reusability Rules
- Must use Python pydantic dataclasses for State and Action objects
- Must use ABC (Abstract Base Class) for Agent, Engine and Validator interfaces
- Must centralize configuration in single YAML file, where the per simulation run, specific Agent, Engine and Validator are specified
- Must use Python's built-in logging module

## Success Criteria
1. Simulation runs for configured number of turns without errors
2. Economic values grow by exact interest rate each turn
3. All actions pass through validation before application
4. State remains consistent throughout simulation
5. Logging captures all major events and state transitions
6. Code passes all unit and integration tests
7. Configuration changes don't require code modifications

## Technical Decisions

### Simplicity Choices
- **YAML for configuration**: Human-readable, no complex parsing required
- **Dataclasses for data objects**: Built-in validation, no boilerplate
- **Single-threaded execution**: Avoids concurrency complexity
- **In-memory state**: No database complexity for MVP
- **Fixed agent strategies**: Removes decision-making complexity

### Reusability Choices
- **ABC base classes**: Agent and Validator can be extended for different behaviors
- **Dataclass inheritance**: State can be extended with additional fields
- **Strategy pattern for agents**: Easy to swap agent implementations
- **Observer pattern for logging**: Decoupled logging from core logic

## Component Specifications

### SimulationEngine
- Loads configuration from YAML
- Manages simulation state
- Orchestrates agent actions
- Applies validation rules
- Applies internal simulation engine rules, these are specified in the specific engine implementation
- Handles termination conditions

### Agent (Base Class)
- Receives state updates
- Generates actions based on state
- MVP: Always returns same action type

### Validator (Base Class)
- Validates actions before application
- Marks actions as validated
- MVP: Always validates successfully

### State (Dataclass)
- Holds current simulation state
- Nation economic_strength values
- Turn counter
- Configuration parameters

### Action (Dataclass)
- Represents agent decisions
- Contains validation flag
- Agent identifier
- Action parameters

### Logger
- Captures simulation events
- Logs state transitions
- Records action validation results
- Outputs to console and/or file