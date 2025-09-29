# Agent Interface Contract

## BaseAgent Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Optional
from llm_sim.models.state import SimulationState
from llm_sim.models.action import Action

class BaseAgent(ABC):
    """Abstract base class for simulation agents."""

    def __init__(self, name: str):
        """Initialize agent with unique name.

        Args:
            name: Unique identifier for this agent
        """
        self.name = name
        self._current_state: Optional[SimulationState] = None

    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide on action based on current state.

        Args:
            state: Current simulation state

        Returns:
            Action to be taken this turn
        """
        pass

    def receive_state(self, state: SimulationState) -> None:
        """Receive state update from engine.

        Args:
            state: New simulation state
        """
        self._current_state = state

    def get_current_state(self) -> Optional[SimulationState]:
        """Get agent's view of current state.

        Returns:
            Current SimulationState or None if not set
        """
        return self._current_state
```

## Contract Requirements

### Initialization
- Must have unique name
- Name must match configuration
- Must be stateless between turns (except current state)

### State Reception
- Must accept any valid SimulationState
- State is read-only for agents
- Must update internal state reference

### Action Decision
- Must return exactly one Action per turn
- Action must include agent name
- Action must have valid action_type
- Decision must be deterministic for testing

### MVP Behavior
- Always return same action type
- No complex decision logic
- No state modification

## Error Handling

### Expected Exceptions
- `ValueError`: Invalid state received
- `RuntimeError`: State not received before action

### Logging Requirements
- Log action decisions
- Log any decision factors
- Log errors with context

## Testing Requirements

### Unit Tests
- Test initialization
- Test state reception
- Test action generation
- Test deterministic behavior

### Integration Tests
- Multiple agents in simulation
- Consistent behavior across turns

## Implementation Example

```python
class NationAgent(BaseAgent):
    """Nation agent for economic simulation."""

    def __init__(self, name: str, strategy: str = "grow"):
        """Initialize nation agent.

        Args:
            name: Nation name
            strategy: Fixed strategy (grow/maintain/decline)
        """
        super().__init__(name)
        self.strategy = strategy

    def decide_action(self, state: SimulationState) -> Action:
        """Return fixed action based on strategy.

        For MVP, always returns same action type.

        Args:
            state: Current simulation state

        Returns:
            Action with agent's strategy
        """
        # MVP: Fixed action based on strategy
        action_type = ActionType.GROW  # Default

        if self.strategy == "maintain":
            action_type = ActionType.MAINTAIN
        elif self.strategy == "decline":
            action_type = ActionType.DECLINE

        return Action(
            agent_name=self.name,
            action_type=action_type,
            parameters={"strength": state.agents[self.name].economic_strength}
        )
```

## Agent Lifecycle

### 1. Initialization
```python
agent = NationAgent(name="Nation_A", strategy="grow")
```

### 2. State Reception
```python
agent.receive_state(current_state)
```

### 3. Action Decision
```python
action = agent.decide_action(current_state)
```

### 4. Action Submission
```python
# Engine collects action
engine.collect_action(action)
```

## Extension Points

### Custom Strategies
Future agents can implement complex strategies:
```python
class SmartAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        # Analyze state
        # Make strategic decision
        # Return optimal action
        pass
```

### State Analysis
Agents can analyze state for decisions:
```python
def analyze_competition(self, state: SimulationState):
    my_strength = state.agents[self.name].economic_strength
    avg_strength = state.global_state.total_economic_value / len(state.agents)
    return my_strength > avg_strength
```