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
        if not action.agent_id:
            return False

        if not action.action_type:
            return False

        # Trade-specific validation
        if action.action_type == "trade":
            if "amount" not in action.action_payload:
                return False

            # Check if agent has enough wealth
            agent_id = action.agent_id
            amount = action.action_payload["amount"]

            # Check wealth from global_state
            agent_wealth = state.global_state.get("agent_wealth", {})
            current_wealth = agent_wealth.get(agent_id, 1000)
            if current_wealth + amount < 0:  # Can't go negative
                return False

        return True
