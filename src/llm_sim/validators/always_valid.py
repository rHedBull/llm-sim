"""Always valid validator implementation."""

from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from llm_sim.utils.logging import get_logger
from llm_sim.validators.base import BaseValidator

logger = get_logger(__name__)


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
            turn=state.turn,
            result="valid",
        )

        return True
