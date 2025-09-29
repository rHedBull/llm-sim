"""Economic simulation engine implementation."""

from typing import Dict, List

from src.llm_sim.engines.base import BaseEngine
from src.llm_sim.models.action import Action
from src.llm_sim.models.state import AgentState, GlobalState, SimulationState
from src.llm_sim.utils.logging import get_logger

logger = get_logger(__name__)


class EconomicEngine(BaseEngine):
    """Economic simulation engine with interest-based growth."""

    def initialize_state(self) -> SimulationState:
        """Create initial state with agents' starting economic values.

        Returns:
            Initial simulation state
        """
        agents: Dict[str, AgentState] = {}
        total_value = 0.0

        for agent_config in self.config.agents:
            agents[agent_config.name] = AgentState(
                name=agent_config.name,
                economic_strength=agent_config.initial_economic_strength,
            )
            total_value += agent_config.initial_economic_strength

        state = SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(
                interest_rate=self.config.engine.interest_rate,
                total_economic_value=total_value,
            ),
        )

        self._state = state
        logger.info(
            "state_initialized",
            turn=0,
            num_agents=len(agents),
            total_value=total_value,
            interest_rate=self.config.engine.interest_rate,
        )

        return state

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions to current state.

        For the MVP, actions don't directly modify state.
        Future versions can implement action effects.

        Args:
            actions: List of validated actions

        Returns:
            Current state (unchanged for MVP)
        """
        if self._state is None:
            raise RuntimeError("Engine state not initialized")

        logger.info("applying_actions", num_actions=len(actions), turn=self._state.turn)

        for action in actions:
            logger.debug(
                "processing_action",
                agent=action.agent_name,
                action_type=action.action_type.value,
                validated=action.validated,
            )

        # MVP: Actions don't change state directly
        # Future: Implement action effects based on action_type
        return self._state

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply interest rate growth to all agents.

        Args:
            state: Current simulation state

        Returns:
            New state with interest applied
        """
        new_agents: Dict[str, AgentState] = {}
        total_value = 0.0
        interest_rate = state.global_state.interest_rate

        for name, agent in state.agents.items():
            new_strength = agent.economic_strength * (1 + interest_rate)
            new_agents[name] = AgentState(name=name, economic_strength=new_strength)
            total_value += new_strength

            logger.debug(
                "applied_interest",
                agent=name,
                old_strength=agent.economic_strength,
                new_strength=new_strength,
                interest_rate=interest_rate,
            )

        new_state = SimulationState(
            turn=state.turn + 1,
            agents=new_agents,
            global_state=GlobalState(interest_rate=interest_rate, total_economic_value=total_value),
        )

        logger.info(
            "engine_rules_applied",
            turn=new_state.turn,
            total_value=total_value,
            interest_rate=interest_rate,
        )

        return new_state

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate.

        Checks:
        1. Max turns reached
        2. Total value below minimum threshold
        3. Total value above maximum threshold

        Args:
            state: Current simulation state

        Returns:
            True if simulation should end
        """
        # Check max turns
        if state.turn >= self.config.simulation.max_turns:
            logger.info(
                "termination_max_turns", turn=state.turn, max_turns=self.config.simulation.max_turns
            )
            return True

        total_value = state.global_state.total_economic_value
        termination = self.config.simulation.termination

        # Check minimum value
        if termination.min_value is not None and total_value < termination.min_value:
            logger.info(
                "termination_min_value",
                total_value=total_value,
                min_value=termination.min_value,
            )
            return True

        # Check maximum value
        if termination.max_value is not None and total_value > termination.max_value:
            logger.info(
                "termination_max_value",
                total_value=total_value,
                max_value=termination.max_value,
            )
            return True

        return False
