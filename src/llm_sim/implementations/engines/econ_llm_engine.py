"""Concrete economic LLM engine implementation."""

from typing import Dict

from llm_sim.infrastructure.patterns.llm_engine import LLMEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model
from llm_sim.models.config import get_variable_definitions


class EconLLMEngine(LLMEngine):
    """Engine that updates economic state based on LLM reasoning."""

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
            agent_data = {"name": agent_config.name}
            if "economic_strength" in agent_var_defs:
                if agent_config.initial_economic_strength is not None:
                    agent_data["economic_strength"] = agent_config.initial_economic_strength
                    total_value += agent_config.initial_economic_strength
                else:
                    agent_data["economic_strength"] = agent_var_defs["economic_strength"].default
                    total_value += agent_var_defs["economic_strength"].default
            agents[agent_config.name] = AgentState(**agent_data)

        # Initialize global state
        global_data = {}
        if "interest_rate" in global_var_defs:
            global_data["interest_rate"] = self.config.engine.interest_rate
        if "total_economic_value" in global_var_defs:
            global_data["total_economic_value"] = total_value
        if "gdp_growth" in global_var_defs:
            global_data["gdp_growth"] = 2.5
        if "inflation" in global_var_defs:
            global_data["inflation"] = 3.0
        if "unemployment" in global_var_defs:
            global_data["unemployment"] = 5.0

        state = SimulationState(
            turn=0,
            agents=agents,
            global_state=GlobalState(**global_data),
            reasoning_chains=[]
        )

        self.current_state = state
        return state

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate.

        Args:
            state: Current simulation state

        Returns:
            True if max turns reached or termination conditions met
        """
        # Check max turns
        if state.turn >= self.config.simulation.max_turns:
            return True

        # Check value thresholds if configured
        total_value = state.global_state.total_economic_value

        if self.config.simulation.termination.min_value is not None:
            if total_value < self.config.simulation.termination.min_value:
                return True

        if self.config.simulation.termination.max_value is not None:
            if total_value > self.config.simulation.termination.max_value:
                return True

        return False

    def _construct_state_update_prompt(self, action: Action, state) -> str:
        """Construct prompt for LLM to calculate new interest rate.

        Args:
            action: Validated action to apply
            state: Current global state (dynamic model)

        Returns:
            Prompt for state update calculation
        """
        SYSTEM_MSG = """You are an economic simulation engine.
Given a validated policy action, determine the new interest rate based on economic theory.

Consider:
- Current economic indicators
- Policy action effects
- Monetary policy principles

Return JSON:
{
  "new_interest_rate": float,
  "reasoning": "step-by-step explanation of how you calculated the new rate",
  "confidence": 0.0-1.0,
  "action_applied": "the action string"
}"""

        USER_MSG = f"""Current state:
- Interest Rate: {state.interest_rate}%
- Inflation: {state.inflation}%
- GDP Growth: {state.gdp_growth}%

Validated action: "{action.action_name}"

Think step-by-step:
1. How does this action affect monetary policy?
2. What interest rate adjustment is appropriate?
3. What is the new interest rate?

Calculate the new interest rate."""

        return SYSTEM_MSG + "\n\n" + USER_MSG

    def _apply_state_update(
        self, decision: StateUpdateDecision, state: SimulationState
    ) -> SimulationState:
        """Apply interest rate update to state.

        Args:
            decision: LLM decision with new interest rate
            state: Current simulation state

        Returns:
            New state with updated interest rate (turn NOT incremented here)
        """
        # Update only interest_rate (economic domain)
        # NOTE: turn is NOT incremented here - it's incremented once per turn in run_turn
        new_global = state.global_state.model_copy(
            update={"interest_rate": decision.new_interest_rate}
        )

        return SimulationState(
            turn=state.turn,  # Keep same turn - incremented once in run_turn
            agents=state.agents,
            global_state=new_global,
            reasoning_chains=[]  # Will be populated by run_turn
        )
