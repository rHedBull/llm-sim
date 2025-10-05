"""Simple economic engine for testing."""

from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState


class SimpleEconomicEngine(BaseEngine):
    """Minimal economic simulation engine for testing."""

    def __init__(self, config: SimulationConfig):
        """Initialize engine."""
        super().__init__(config)
        self.max_turns = 10  # Default max turns

    def initialize_state(self) -> SimulationState:
        """Create initial simulation state.

        Returns:
            Initial SimulationState
        """
        # Get global_state from config if available, otherwise use default
        global_state = getattr(self.config, 'global_state', None) or {"turn": 0}

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
        if self._state is None:
            raise RuntimeError("State not initialized")

        # Create mutable copy of global_state
        new_global_state = dict(self._state.global_state)

        # Process actions
        for action in actions:
            if action.action_type == "trade":
                # Simple trade processing
                payload = action.action_payload
                if "amount" in payload:
                    # Update agent's wealth (simplified - just track in global_state)
                    agent_id = action.agent_id
                    if "agent_wealth" not in new_global_state:
                        new_global_state["agent_wealth"] = {}

                    current_wealth = new_global_state.get("agent_wealth", {}).get(agent_id, 1000)
                    if "agent_wealth" not in new_global_state:
                        new_global_state["agent_wealth"] = {}
                    new_global_state["agent_wealth"][agent_id] = current_wealth + payload["amount"]

        return SimulationState(
            turn=self._state.turn,
            agents=self._state.agents,
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
        # Create new global_state dict with updated turn
        new_global_state = dict(state.global_state)
        new_global_state["turn"] = state.turn + 1

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
