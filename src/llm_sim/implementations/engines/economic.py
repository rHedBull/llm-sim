"""Economic simulation engine implementation."""

from typing import Dict, List

from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model
from llm_sim.models.config import get_variable_definitions
from llm_sim.utils.logging import get_logger

logger = get_logger(__name__)


class EconomicEngine(BaseEngine):
    """Economic simulation engine with interest-based growth."""

    def initialize_state(self) -> SimulationState:
        """Create initial state with agents' starting economic values.

        Returns:
            Initial simulation state
        """
        # Get variable definitions from config
        agent_var_defs, global_var_defs = get_variable_definitions(self.config)

        # Create dynamic state models
        AgentState = create_agent_state_model(agent_var_defs)
        GlobalState = create_global_state_model(global_var_defs)

        # Store models for later use
        self._agent_state_model = AgentState
        self._global_state_model = GlobalState

        # Initialize agents
        agents: Dict[str, any] = {}
        total_value = 0.0

        for agent_config in self.config.agents:
            # Create agent with dynamic model (using defaults from variable definitions)
            agent_data = {"name": agent_config.name}

            # For backward compatibility: if economic_strength exists, use initial_economic_strength
            if "economic_strength" in agent_var_defs:
                # Use initial_economic_strength if provided, otherwise use default from variable definition
                if agent_config.initial_economic_strength is not None:
                    agent_data["economic_strength"] = agent_config.initial_economic_strength
                    total_value += agent_config.initial_economic_strength
                else:
                    # Use default from variable definition
                    agent_data["economic_strength"] = agent_var_defs["economic_strength"].default
                    total_value += agent_var_defs["economic_strength"].default

            agents[agent_config.name] = AgentState(**agent_data)

        # Initialize global state with dynamic model
        global_data = {}

        # For backward compatibility: populate interest_rate and total_economic_value if they exist
        if "interest_rate" in global_var_defs:
            global_data["interest_rate"] = self.config.engine.interest_rate
        if "total_economic_value" in global_var_defs:
            global_data["total_economic_value"] = total_value

        state = SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(**global_data),
        )

        self._state = state
        logger.info(
            "state_initialized",
            turn=0,
            num_agents=len(agents),
            total_value=total_value if "total_economic_value" in global_var_defs else None,
            interest_rate=self.config.engine.interest_rate if "interest_rate" in global_var_defs else None,
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
                action_name=action.action_name,
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
        new_agents: Dict[str, any] = {}
        total_value = 0.0

        # Only apply economic rules if economic_strength and interest_rate exist
        if not hasattr(state.global_state, "interest_rate"):
            # No economic simulation - just increment turn
            return SimulationState(
                turn=state.turn + 1,
                agents=state.agents,
                global_state=state.global_state,
            )

        interest_rate = state.global_state.interest_rate

        # Apply interest to agents with economic_strength
        for name, agent in state.agents.items():
            if hasattr(agent, "economic_strength"):
                new_strength = agent.economic_strength * (1 + interest_rate)
                new_agents[name] = self._agent_state_model(name=name, economic_strength=new_strength)
                total_value += new_strength

                logger.debug(
                    "applied_interest",
                    agent=name,
                    old_strength=agent.economic_strength,
                    new_strength=new_strength,
                    interest_rate=interest_rate,
                )
            else:
                # Agent doesn't have economic_strength - copy as-is
                new_agents[name] = agent

        # Update global state
        global_data = state.global_state.model_dump()
        global_data["interest_rate"] = interest_rate
        if "total_economic_value" in global_data:
            global_data["total_economic_value"] = total_value

        new_state = SimulationState(
            turn=state.turn + 1,
            agents=new_agents,
            global_state=self._global_state_model(**global_data),
        )

        logger.info(
            "engine_rules_applied",
            turn=new_state.turn,
            total_value=total_value if hasattr(state.global_state, "total_economic_value") else None,
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

        # Check termination conditions if they exist
        if termination is not None:
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
