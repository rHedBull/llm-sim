"""Nation agent implementation."""

from llm_sim.agents.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from llm_sim.utils.logging import get_logger

logger = get_logger(__name__)


class NationAgent(BaseAgent):
    """Nation agent for economic simulation."""

    def __init__(self, name: str, strategy: str = "grow") -> None:
        """Initialize nation agent.

        Args:
            name: Nation name
            strategy: Fixed strategy (grow/maintain/decline)

        Raises:
            ValueError: If strategy is not valid
        """
        super().__init__(name)

        valid_strategies = {"grow", "maintain", "decline"}
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy '{strategy}'. Must be one of {valid_strategies}")

        self.strategy = strategy
        logger.info("nation_agent_initialized", name=name, strategy=strategy)

    def decide_action(self, state: SimulationState) -> Action:
        """Return fixed action based on strategy.

        For MVP, always returns same action type based on strategy.

        Args:
            state: Current simulation state

        Returns:
            Action with agent's strategy

        Raises:
            KeyError: If agent not found in state
        """
        if self.name not in state.agents:
            raise KeyError(f"Agent '{self.name}' not found in state")

        action_name = self.strategy  # Use strategy directly as action name

        current_strength = state.agents[self.name].economic_strength

        action = Action(
            agent_name=self.name,
            action_name=action_name,
            parameters={"strength": current_strength},
        )

        logger.debug(
            "action_decided",
            agent=self.name,
            action=action_name,
            strength=current_strength,
            turn=state.turn,
        )

        return action
