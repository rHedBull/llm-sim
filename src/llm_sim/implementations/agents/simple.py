"""Simple agent for testing."""

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class SimpleAgent(BaseAgent):
    """Minimal agent for testing."""

    def __init__(self, name: str, config: dict = None):
        """Initialize agent.

        Args:
            name: Agent name
            config: Agent configuration
        """
        super().__init__(name)
        self.config = config or {}

    def decide_action(self, state: SimulationState) -> Action:
        """Decide action based on state.

        Args:
            state: Current simulation state

        Returns:
            Action to take
        """
        # Simple action: trade based on turn
        # Get wealth from global_state (it's a BaseModel)
        agent_wealth = getattr(state.global_state, 'agent_wealth', {}).get(self.name, 1000)

        # Alternate between positive and negative trades based on turn
        if state.turn % 2 == 0:
            amount = 10
        else:
            amount = -5

        return Action(
            agent_name=self.name,
            action_name="trade",
            parameters={"amount": amount},
            validated=False  # Will be validated by validator
        )
