"""Economic domain LLM validator implementation."""

from llm_sim.models.action import Action
from llm_sim.utils.llm_client import LLMClient
from llm_sim.validators.llm_validator import LLMValidator


class EconLLMValidator(LLMValidator):
    """LLM-based validator for economic policy domain.

    Validates actions against economic policy boundaries using structured
    LLM outputs. Uses permissive validation by default (FR-005a).

    Economic domain includes: interest rates, fiscal policy, trade policy,
    taxation, monetary policy, economic sanctions.

    Non-economic domains: military actions, social policy, foreign diplomacy
    (unless economically focused).
    """

    def __init__(self, llm_client: LLMClient, domain: str = "economic", permissive: bool = True) -> None:
        """Initialize economic domain validator.

        Args:
            llm_client: LLM client for validation calls
            domain: Domain name (defaults to "economic")
            permissive: If True, return all actions with validation results.
                       If False, filter out invalid actions.
        """
        super().__init__(llm_client=llm_client, domain=domain, permissive=permissive)

    def _get_domain_description(self) -> str:
        """Get description of economic domain boundaries.

        Returns:
            Domain description string defining economic policy boundaries
        """
        return """Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused)."""

    def _construct_validation_prompt(self, action: Action) -> str:
        """Construct validation prompt for economic domain.

        Args:
            action: Action to validate

        Returns:
            Validation prompt string with system message and user query
        """
        SYSTEM_MSG = """You are a policy domain validator.
Determine if a proposed action falls within the ECONOMIC policy domain.

Economic domain includes: interest rates, fiscal policy, trade policy, taxation, monetary policy, economic sanctions.
NON-economic domains: military actions, social policy, foreign diplomacy (unless economically focused).

Use permissive validation: accept if the action has ANY significant economic impact, even if it touches other domains.

Return JSON:
{
  "is_valid": true/false,
  "reasoning": "step-by-step explanation of domain determination",
  "confidence": 0.0-1.0,
  "action_evaluated": "the action string"
}"""

        USER_MSG = f"""Proposed action: "{action.action_string}"

Think step-by-step:
1. What is the primary domain of this action?
2. Does it have significant economic impact?
3. Is it within the economic policy domain?

Validate this action."""

        return SYSTEM_MSG + "\n\n" + USER_MSG