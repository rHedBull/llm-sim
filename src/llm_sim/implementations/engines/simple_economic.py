"""Simple economic engine for testing."""

from pydantic import BaseModel
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState


class SimpleGlobalState(BaseModel):
    """Simple global state for testing."""
    turn: int = 0
    agent_wealth: dict = {}


class SimpleEconomicEngine(BaseEngine):
    """Minimal economic simulation engine for testing."""

    def __init__(self, config: SimulationConfig):
        """Initialize engine."""
        super().__init__(config)
        self.max_turns = 10  # Default max turns
        # Initialize state on construction
        self._state = self.initialize_state()

    def initialize_state(self) -> SimulationState:
        """Create initial simulation state.

        Returns:
            Initial SimulationState
        """
        # Create global state as BaseModel
        global_state = SimpleGlobalState(turn=0, agent_wealth={})

        return SimulationState(
            turn=0,
            agents={},  # Maps agent_id -> agent state model
            global_state=global_state
        )

    def apply_actions(self, actions: list[Action]) -> SimulationState:
        """Apply validated actions to state.

        Args:
            actions: List of validated actions

        Returns:
            Updated SimulationState
        """
        # Get current state - orchestrator passes it via BaseEngine.run_turn
        state = self.get_current_state()

        # Get current wealth dict
        current_global: SimpleGlobalState = state.global_state
        agent_wealth = dict(current_global.agent_wealth)

        # Process actions
        for action in actions:
            if action.action_name == "trade":
                # Simple trade processing
                params = action.parameters
                if params and "amount" in params:
                    # Update agent's wealth
                    agent_name = action.agent_name
                    current_wealth = agent_wealth.get(agent_name, 1000)
                    agent_wealth[agent_name] = current_wealth + params["amount"]

        # Create new global state
        new_global_state = SimpleGlobalState(
            turn=current_global.turn,
            agent_wealth=agent_wealth
        )

        return SimulationState(
            turn=state.turn,
            agents=state.agents,
            global_state=new_global_state
        )

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine rules.

        Args:
            state: Current state

        Returns:
            State after engine rules
        """
        # Simple increment turn counter
        current_global: SimpleGlobalState = state.global_state
        new_global_state = SimpleGlobalState(
            turn=state.turn + 1,
            agent_wealth=dict(current_global.agent_wealth)
        )

        return SimulationState(
            turn=state.turn + 1,
            agents=state.agents,
            global_state=new_global_state
        )

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should end.

        Args:
            state: Current state

        Returns:
            True if should terminate
        """
        return state.turn >= self.max_turns
