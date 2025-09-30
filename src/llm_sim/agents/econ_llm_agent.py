"""Concrete economic LLM agent implementation."""

from llm_sim.agents.llm_agent import LLMAgent
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState


class EconLLMAgent(LLMAgent):
    """Agent that generates economic policy actions using LLM reasoning."""

    def _construct_prompt(self, state: SimulationState) -> str:
        """Construct economic policy prompt for LLM.

        Args:
            state: Current simulation state

        Returns:
            Prompt string with economic indicators
        """
        SYSTEM_MSG = """You are an economic policy advisor for a nation.
Analyze the current economic state and propose ONE specific policy action.
Think step-by-step about the economic situation and reasoning behind your recommendation.

Return your response as JSON with this structure:
{
  "action": "specific policy action string",
  "reasoning": "step-by-step explanation of why this action is appropriate",
  "confidence": 0.0-1.0
}"""

        USER_MSG = f"""Current economic state:
- GDP Growth: {state.global_state.gdp_growth}%
- Inflation: {state.global_state.inflation}%
- Unemployment: {state.global_state.unemployment}%
- Interest Rate: {state.global_state.interest_rate}%

Think step-by-step:
1. What is the most pressing economic issue?
2. What policy action would address this issue?
3. What are the expected effects?

Propose ONE specific economic policy action."""

        return SYSTEM_MSG + "\n\n" + USER_MSG

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Validate that decision is economic in nature.

        Args:
            decision: LLM-generated policy decision

        Returns:
            Always True - let the LLM validator handle domain validation
        """
        # Agent-side validation removed - LLM validator is smart enough
        # to determine if actions are within the economic domain
        return True
