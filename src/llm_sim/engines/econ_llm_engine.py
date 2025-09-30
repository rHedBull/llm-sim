"""Economic LLM-based engine concrete implementation."""

from typing import List

from llm_sim.engines.llm_engine import LLMEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision
from llm_sim.models.state import GlobalState, SimulationState


class EconLLMEngine(LLMEngine):
    """Concrete LLM engine for economic simulation.

    Implements economic domain-specific logic for:
    - State update prompts with monetary policy reasoning
    - Interest rate updates based on validated policy actions
    """

    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        """Construct economic domain-specific state update prompt.

        Args:
            action: Validated action to apply
            state: Current global state

        Returns:
            Full prompt string for LLM state reasoning
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
        self,
        decision: StateUpdateDecision,
        state: SimulationState
    ) -> SimulationState:
        """Apply economic domain-specific state update.

        Updates only the interest_rate field (economic domain).
        Note: Turn incrementation happens in run_turn, not here.

        Args:
            decision: LLM-generated state update decision
            state: Current simulation state

        Returns:
            New SimulationState with interest_rate updated
        """
        # Update only interest_rate (economic domain)
        new_global = state.global_state.model_copy(
            update={"interest_rate": decision.new_interest_rate}
        )

        return SimulationState(
            turn=state.turn,  # Keep same turn - will be incremented in run_turn override
            agents=state.agents,
            global_state=new_global,
            reasoning_chains=[]  # Will be populated by run_turn
        )

    async def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        """Execute one simulation turn using LLM reasoning.

        Overrides base run_turn to handle turn incrementation properly.
        Turn is incremented once per run_turn call, not per action.

        Args:
            validated_actions: List of actions (may include unvalidated actions)

        Returns:
            New SimulationState with updated state and reasoning chains
        """
        # Call parent run_turn to process actions
        new_state = await super().run_turn(validated_actions)

        # Increment turn once at the end of the turn processing
        return new_state.model_copy(update={"turn": new_state.turn + 1})