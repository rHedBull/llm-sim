"""Concrete economic LLM engine implementation."""

from llm_sim.engines.llm_engine import LLMEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import SimulationState, GlobalState


class EconLLMEngine(LLMEngine):
    """Engine that updates economic state based on LLM reasoning."""

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

Validated action: "{action.action_string}"

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
            New state with updated interest rate
        """
        # Update only interest_rate (economic domain)
        new_global = state.global_state.model_copy(
            update={"interest_rate": decision.new_interest_rate}
        )

        return SimulationState(
            turn=state.turn + 1,
            agents=state.agents,
            global_state=new_global,
            reasoning_chains=[]  # Will be populated by run_turn
        )
