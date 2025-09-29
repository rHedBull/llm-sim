# Validator Interface Contract

## BaseValidator Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import List
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class BaseValidator(ABC):
    """Abstract base class for action validators."""

    def __init__(self):
        """Initialize validator."""
        self.validation_count = 0
        self.rejection_count = 0

    @abstractmethod
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate single action against current state.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            True if action is valid, False otherwise
        """
        pass

    def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        """Validate and mark all actions.

        Args:
            actions: List of actions to validate
            state: Current simulation state

        Returns:
            List of validated actions (may be subset of input)
        """
        validated = []

        for action in actions:
            if self.validate_action(action, state):
                validated.append(action.mark_validated())
                self.validation_count += 1
            else:
                self.rejection_count += 1

        return validated

    def get_stats(self) -> dict:
        """Get validation statistics.

        Returns:
            Dictionary with validation stats
        """
        return {
            "total_validated": self.validation_count,
            "total_rejected": self.rejection_count,
            "acceptance_rate": self.validation_count / (self.validation_count + self.rejection_count)
            if (self.validation_count + self.rejection_count) > 0 else 0
        }
```

## Contract Requirements

### Validation Logic
- Must be deterministic
- Must not modify action or state
- Must return boolean result
- Must handle all action types

### Action Marking
- Valid actions must be marked with timestamp
- Invalid actions must not be marked
- Original action must not be modified

### State Access
- State is read-only
- Must validate against current state
- Must handle missing agents gracefully

### MVP Behavior
- Always validates successfully
- Logs all validation attempts
- Maintains statistics

## Error Handling

### Expected Exceptions
- `ValueError`: Malformed action
- `KeyError`: Unknown agent in action

### Logging Requirements
- Log each validation attempt
- Log validation result
- Log rejection reasons
- Log statistics periodically

## Testing Requirements

### Unit Tests
- Test validation logic
- Test action marking
- Test statistics tracking
- Test error cases

### Integration Tests
- Multiple actions per turn
- Invalid actions handling
- Statistics accuracy

## Implementation Example

```python
class AlwaysValidValidator(BaseValidator):
    """MVP validator that accepts all actions."""

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Always validates actions for MVP.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            Always True for MVP
        """
        # MVP: Always valid
        # In production, would check:
        # - Agent exists in state
        # - Action parameters are valid
        # - Action doesn't violate game rules

        logger.info(
            "validating_action",
            agent=action.agent_name,
            action_type=action.action_type.value,
            turn=state.turn
        )

        return True


class RulesValidator(BaseValidator):
    """Production validator with actual rules."""

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate action against game rules.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            True if valid, False otherwise
        """
        # Check agent exists
        if action.agent_name not in state.agents:
            logger.warning(
                "invalid_agent",
                agent=action.agent_name,
                known_agents=list(state.agents.keys())
            )
            return False

        # Check action type is valid
        if action.action_type not in ActionType:
            logger.warning(
                "invalid_action_type",
                action_type=action.action_type,
                valid_types=[t.value for t in ActionType]
            )
            return False

        # Additional rules...
        return True
```

## Validation Flow

### 1. Action Collection
```python
actions = [agent.decide_action(state) for agent in agents]
```

### 2. Validation
```python
validated_actions = validator.validate_actions(actions, state)
```

### 3. Application
```python
new_state = engine.apply_actions(validated_actions)
```

## Extension Points

### Custom Rules
Validators can implement complex rules:
```python
class EconomicValidator(BaseValidator):
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        # Check economic constraints
        # Verify resource availability
        # Validate transaction limits
        pass
```

### Context-Aware Validation
Validators can consider global context:
```python
def validate_with_context(self, action: Action, state: SimulationState) -> bool:
    # Check global economic health
    # Verify action doesn't destabilize system
    # Consider other pending actions
    pass
```

## Statistics Tracking

### Metrics
- Total validations
- Total rejections
- Acceptance rate
- Rejection reasons
- Performance timing

### Reporting
```python
stats = validator.get_stats()
logger.info("validation_stats", **stats)
```