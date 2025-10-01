# Base Classes Reference

The base classes define the core interfaces for simulation components. All concrete implementations must extend these abstract classes.

## BaseAgent

The `BaseAgent` class defines the interface for all simulation agents.

**Location**: `llm_sim.infrastructure.base.agent`

### Interface

```python
from abc import ABC, abstractmethod
from typing import Optional
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class BaseAgent(ABC):
    """Abstract base class for simulation agents."""

    def __init__(self, name: str) -> None:
        """Initialize agent with unique name."""
        self.name = name
        self._current_state: Optional[SimulationState] = None

    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide on action based on current state.

        Must be implemented by subclasses to define agent behavior.
        """
        pass

    def receive_state(self, state: SimulationState) -> None:
        """Receive state update from engine (optional override)."""
        self._current_state = state

    def get_current_state(self) -> Optional[SimulationState]:
        """Get agent's view of current state."""
        return self._current_state
```

### Required Methods

- **`decide_action(state: SimulationState) -> Action`**: Must return an Action based on the current simulation state

### Optional Methods

- **`receive_state(state: SimulationState)`**: Override to process state updates
- **`get_current_state()`**: Access the agent's cached state

### Example Implementation

```python
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class SimpleAgent(BaseAgent):
    """Example agent with fixed strategy."""

    def __init__(self, name: str, strategy: str = "grow"):
        super().__init__(name=name)
        self.strategy = strategy

    def decide_action(self, state: SimulationState) -> Action:
        """Return action based on fixed strategy."""
        return Action(
            agent_name=self.name,
            action_name=self.strategy,
            parameters={}
        )
```

## BaseEngine

The `BaseEngine` class defines the interface for simulation engines that manage state and apply rules.

**Location**: `llm_sim.infrastructure.base.engine`

### Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState

class BaseEngine(ABC):
    """Abstract base class for simulation engines."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self._state: Optional[SimulationState] = None
        self._turn_counter: int = 0

    @abstractmethod
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state from configuration."""
        pass

    @abstractmethod
    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions to current state."""
        pass

    @abstractmethod
    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine-specific rules (e.g., interest growth)."""
        pass

    @abstractmethod
    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate."""
        pass

    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute one simulation turn (implements default flow)."""
        new_state = self.apply_actions(actions)
        new_state = self.apply_engine_rules(new_state)
        self._state = new_state
        self._turn_counter += 1
        return new_state
```

### Required Methods

- **`initialize_state() -> SimulationState`**: Create initial state from config
- **`apply_actions(actions) -> SimulationState`**: Process agent actions
- **`apply_engine_rules(state) -> SimulationState`**: Apply game mechanics
- **`check_termination(state) -> bool`**: Determine when simulation ends

### Optional Methods

- **`run_turn(actions) -> SimulationState`**: Override to customize turn flow

### Example Implementation

```python
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.state import SimulationState, AgentState, GlobalState

class SimpleEconomicEngine(BaseEngine):
    """Example engine with basic economic rules."""

    def initialize_state(self) -> SimulationState:
        """Create initial state with agents from config."""
        agents = {
            agent_config.name: AgentState(
                name=agent_config.name,
                economic_strength=agent_config.initial_economic_strength
            )
            for agent_config in self.config.agents
        }
        return SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(
                interest_rate=self.config.engine.interest_rate,
                total_economic_value=sum(a.economic_strength for a in agents.values())
            )
        )

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply economic actions to state."""
        # Implementation here
        return self._state

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply interest growth."""
        # Implementation here
        return state

    def check_termination(self, state: SimulationState) -> bool:
        """Check if max turns reached."""
        return state.turn >= self.config.simulation.max_turns
```

## BaseValidator

The `BaseValidator` class defines the interface for action validation.

**Location**: `llm_sim.infrastructure.base.validator`

### Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class BaseValidator(ABC):
    """Abstract base class for action validators."""

    def __init__(self) -> None:
        self.validation_count: int = 0
        self.rejection_count: int = 0

    @abstractmethod
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate single action against current state."""
        pass

    def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        """Validate and mark all actions (implements default batch logic)."""
        validated: List[Action] = []
        for action in actions:
            if self.validate_action(action, state):
                validated.append(action.mark_validated())
                self.validation_count += 1
            else:
                self.rejection_count += 1
        return validated

    def get_stats(self) -> Dict[str, float]:
        """Get validation statistics."""
        total = self.validation_count + self.rejection_count
        acceptance_rate = self.validation_count / total if total > 0 else 0.0
        return {
            "total_validated": float(self.validation_count),
            "total_rejected": float(self.rejection_count),
            "acceptance_rate": acceptance_rate,
        }
```

### Required Methods

- **`validate_action(action, state) -> bool`**: Return True if action is valid

### Optional Methods

- **`validate_actions(actions, state) -> List[Action]`**: Override for batch validation
- **`get_stats() -> Dict[str, float]`**: Access validation statistics

### Example Implementation

```python
from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class AlwaysValidValidator(BaseValidator):
    """Example validator that accepts all actions."""

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Always return True."""
        return True
```

## Best Practices

1. **Always call `super().__init__()`** in your constructors
2. **Use type hints** for all method parameters and return values
3. **Document your methods** with clear docstrings
4. **Raise appropriate exceptions** for invalid states
5. **Keep state immutable** - return new state objects rather than modifying

## See Also

- [LLM Pattern Documentation](llm_pattern.md) - Higher-level patterns built on these bases
- [Creating Implementations](creating_implementations.md) - Guide to creating custom components
