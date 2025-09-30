"""Concrete economic LLM validator implementation."""

from typing import TYPE_CHECKING

from llm_sim.validators.llm_validator import LLMValidator
from llm_sim.models.action import Action

if TYPE_CHECKING:
    from llm_sim.models.state import SimulationState


class EconLLMValidator(LLMValidator):
    """Validator that checks if actions are within economic policy domain."""

    def _get_domain_description(self) -> str:
        """Get economic domain boundaries.

        Returns:
            Description of what is/isn't economic policy
        """
        return """Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused)."""

    def _construct_validation_prompt(self, action: Action, state: "SimulationState") -> str:
        """Construct validation prompt for economic domain.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            Prompt asking LLM to validate domain
        """
        permissive_note = ""
        if self.permissive:
            permissive_note = "\nUse permissive validation: accept if the action has ANY significant economic impact, even if it touches other domains."

        SYSTEM_MSG = f"""You are a policy domain validator.
Determine if a proposed action falls within the ECONOMIC policy domain.

Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).
{permissive_note}

Return JSON:
{{
  "is_valid": true/false,
  "reasoning": "step-by-step explanation of domain determination",
  "confidence": 0.0-1.0,
  "action_evaluated": "the action string"
}}"""

        USER_MSG = f"""Proposed action: "{action.action_name}"

Think step-by-step:
1. What is the primary domain of this action?
2. Does it have significant economic impact?
3. Is it within the economic policy domain?

Validate this action."""

        return SYSTEM_MSG + "\n\n" + USER_MSG
