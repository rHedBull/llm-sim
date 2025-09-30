# BaseAgent Contract

**Component**: `llm_sim.infrastructure.base.agent.BaseAgent`
**Type**: Abstract Base Class
**Purpose**: Minimal interface for all simulation agents

## Interface Contract

### Class Definition
```python
from abc import ABC, abstractmethod
from typing import Optional

class BaseAgent(ABC):
    """Abstract base class for simulation agents."""
```

### Required Attributes
- `name: str` - Unique identifier for the agent
- `_current_state: Optional[SimulationState]` - Agent's view of current state

### Required Methods

#### `__init__(self, name: str) -> None`
**Purpose**: Initialize agent with unique name
**Parameters**:
- `name: str` - Unique identifier for this agent
**Postconditions**:
- `self.name` is set
- `self._current_state` is None

#### `decide_action(self, state: SimulationState) -> Action` (ABSTRACT)
**Purpose**: Decide on action based on current state
**Parameters**:
- `state: SimulationState` - Current simulation state
**Returns**: `Action` - Action to be taken this turn
**Constraints**:
- Must be implemented by concrete classes
- Must return a valid Action object
- Should not mutate the input state

#### `receive_state(self, state: SimulationState) -> None`
**Purpose**: Receive state update from engine
**Parameters**:
- `state: SimulationState` - New simulation state
**Side Effects**:
- Updates `self._current_state`

#### `get_current_state(self) -> Optional[SimulationState]`
**Purpose**: Get agent's view of current state
**Returns**: `Optional[SimulationState]` - Current state or None if not set
**Constraints**:
- Returns None if `receive_state` has never been called
- Returns most recent state otherwise

## Inheritance Contract

### For Concrete Implementations
Concrete classes extending `BaseAgent` MUST:
1. Call `super().__init__(name)` in their `__init__`
2. Implement `decide_action` method
3. Optionally override `receive_state` if additional state handling needed
4. Not break Liskov Substitution Principle

### Example Valid Implementation
```python
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class MyAgent(BaseAgent):
    def __init__(self, name: str, strategy: str):
        super().__init__(name)
        self.strategy = strategy

    def decide_action(self, state: SimulationState) -> Action:
        # Domain-specific logic here
        return Action(agent_name=self.name, action_name=self.strategy)
```

## Breaking Changes

Changes to this interface are BREAKING and require major version bump:
- Adding required abstract methods
- Changing method signatures
- Removing or renaming public attributes
- Changing return types

## Non-Breaking Changes

These changes are NON-BREAKING:
- Adding optional methods with default implementations
- Adding private attributes (prefixed with `_`)
- Improving docstrings
- Adding type hints

## Validation Tests

Contract tests MUST verify:
1. `BaseAgent` is abstract (cannot be instantiated)
2. `decide_action` is abstract method
3. `receive_state` has default implementation
4. `get_current_state` returns None initially
5. Concrete implementations can be instantiated
6. Concrete implementations must implement `decide_action`

## Dependencies

**Required Models**:
- `SimulationState` from `llm_sim.models.state`
- `Action` from `llm_sim.models.action`

**No External Dependencies** - Uses only Python stdlib and project models
