"""Basic validator for testing."""

from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class BasicValidator(BaseValidator):
    """Minimal validator for testing."""

    def __init__(self, config: dict = None):
        """Initialize validator."""
        super().__init__()
        self.config = config or {}

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate an action.

        Args:
            state: Current simulation state
            action: Action to validate

        Returns:
            True if action is valid
        """
        # Basic validation - check action has required fields
        if not action.agent_name:
            return False

        if not action.action_name:
            return False

        # Trade-specific validation
        if action.action_name == "trade":
            if not action.parameters or "amount" not in action.parameters:
                return False

            # Check if agent has enough wealth
            agent_name = action.agent_name
            amount = action.parameters["amount"]

            # Check wealth from global_state (it's a BaseModel)
            agent_wealth_dict = getattr(state.global_state, 'agent_wealth', {})
            current_wealth = agent_wealth_dict.get(agent_name, 1000)
            if current_wealth + amount < 0:  # Can't go negative
                return False

        return True
