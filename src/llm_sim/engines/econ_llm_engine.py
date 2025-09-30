"""Concrete economic LLM engine implementation."""

from typing import Dict

from llm_sim.engines.llm_engine import LLMEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import SimulationState, GlobalState, AgentState


class EconLLMEngine(LLMEngine):
    """Engine that updates economic state based on LLM reasoning."""

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
                gdp_growth=2.5,  # Default initial values
                inflation=3.0,
                unemployment=5.0,
            ),
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

    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        """Construct prompt for LLM to calculate new interest rate.

        Args:
            action: Validated action to apply
            state: Current global state

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
