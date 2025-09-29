# Engine Interface Contract

## BaseEngine Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from llm_sim.models.state import SimulationState
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig

class BaseEngine(ABC):
    """Abstract base class for simulation engines."""

    def __init__(self, config: SimulationConfig):
        """Initialize engine with configuration."""
        self.config = config
        self._state: Optional[SimulationState] = None
        self._turn_counter: int = 0

    @abstractmethod
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state from configuration.

        Returns:
            Initial SimulationState object
        """
        pass

    @abstractmethod
    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions to current state.

        Args:
            actions: List of validated actions from agents

        Returns:
            New SimulationState after applying actions
        """
        pass

    @abstractmethod
    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine-specific rules (e.g., interest growth).

        Args:
            state: Current simulation state

        Returns:
            New SimulationState after applying engine rules
        """
        pass

    @abstractmethod
    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate.

        Args:
            state: Current simulation state

        Returns:
            True if simulation should end, False otherwise
        """
        pass

    def get_current_state(self) -> SimulationState:
        """Get current simulation state.

        Returns:
            Current SimulationState

        Raises:
            RuntimeError: If state not initialized
        """
        if self._state is None:
            raise RuntimeError("Engine state not initialized")
        return self._state

    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute one simulation turn.

        Args:
            actions: Validated actions from all agents

        Returns:
            New state after turn execution
        """
        # Apply actions
        new_state = self.apply_actions(actions)

        # Apply engine rules
        new_state = self.apply_engine_rules(new_state)

        # Update internal state
        self._state = new_state
        self._turn_counter += 1

        return new_state
```

## Contract Requirements

### Initialization
- Must accept SimulationConfig
- Must validate configuration on init
- Must create valid initial state

### State Management
- State must be immutable
- Each turn produces new state
- State transitions must be logged

### Action Processing
- Only process validated actions
- Actions applied in deterministic order
- Invalid actions must raise exceptions

### Engine Rules
- Applied after all actions
- Must be deterministic
- Must preserve state consistency

### Termination
- Check after each turn
- Support max_turns limit
- Support value thresholds

## Error Handling

### Expected Exceptions
- `ValueError`: Invalid configuration
- `RuntimeError`: State not initialized
- `TypeError`: Wrong action/state types

### Logging Requirements
- Log each state transition
- Log termination conditions
- Log any errors with context

## Testing Requirements

### Unit Tests
- Test initialization with valid/invalid configs
- Test action application
- Test engine rules
- Test termination conditions

### Integration Tests
- Full simulation run
- Multiple agents
- Various termination scenarios

## Implementation Example

```python
class EconomicEngine(BaseEngine):
    """Economic simulation engine with interest-based growth."""

    def initialize_state(self) -> SimulationState:
        """Create initial state with agents' starting economic values."""
        agents = {}
        for agent_config in self.config.agents:
            agents[agent_config.name] = AgentState(
                name=agent_config.name,
                economic_strength=agent_config.initial_economic_strength
            )

        return SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(
                interest_rate=self.config.engine.interest_rate,
                total_economic_value=sum(a.economic_strength for a in agents.values())
            )
        )

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply interest rate growth to all agents."""
        new_agents = {}
        for name, agent in state.agents.items():
            new_strength = agent.economic_strength * (1 + state.global_state.interest_rate)
            new_agents[name] = AgentState(
                name=name,
                economic_strength=new_strength
            )

        return SimulationState(
            turn=state.turn + 1,
            agents=new_agents,
            global_state=GlobalState(
                interest_rate=state.global_state.interest_rate,
                total_economic_value=sum(a.economic_strength for a in new_agents.values())
            )
        )
```