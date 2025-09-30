"""LLM-based validator using structured LLM outputs for domain validation."""

from abc import abstractmethod
from typing import List

import structlog

from llm_sim.models.action import Action
from llm_sim.models.llm_models import ValidationResult
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient
from llm_sim.validators.base import BaseValidator

logger = structlog.get_logger()


class LLMValidator(BaseValidator):
    """Abstract base class for LLM-based action validators.

    This validator uses an LLM to validate actions against domain-specific boundaries.
    Subclasses must implement:
    - _construct_validation_prompt: Build the validation prompt for a specific action
    - _get_domain_description: Provide domain boundaries description

    The validator operates in 'permissive' mode by default (FR-005a), marking actions
    with validation results but not filtering them out.
    """

    def __init__(self, llm_client: LLMClient, domain: str, permissive: bool = True) -> None:
        """Initialize LLM validator.

        Args:
            llm_client: LLM client for validation calls
            domain: Domain name (e.g., "economic")
            permissive: If True, return all actions with validation results.
                       If False, filter out invalid actions.
        """
        super().__init__()
        self.llm_client = llm_client
        self.domain = domain
        self.permissive = permissive

    @abstractmethod
    def _construct_validation_prompt(self, action: Action) -> str:
        """Construct domain-specific validation prompt for an action.

        Args:
            action: Action to validate

        Returns:
            Validation prompt string
        """
        pass

    @abstractmethod
    def _get_domain_description(self) -> str:
        """Get description of domain boundaries.

        Returns:
            Domain description string
        """
        pass

    async def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        """Validate actions using LLM-based domain validation.

        This method:
        1. Loops through all actions
        2. Constructs validation prompt for each action
        3. Calls LLM to validate action against domain boundaries
        4. Marks action.validated based on result.is_valid
        5. Sets action.validation_result
        6. Logs reasoning chain at DEBUG level

        Args:
            actions: List of actions to validate
            state: Current simulation state

        Returns:
            List of validated actions (same length as input in permissive mode)
        """
        validated_actions: List[Action] = []

        for action in actions:
            # Construct validation prompt using domain-specific logic
            prompt = self._construct_validation_prompt(action)

            # Call LLM to validate action
            result: ValidationResult = await self.llm_client.call_with_retry(
                prompt=prompt,
                response_model=ValidationResult,
                component="validator"
            )

            # Log reasoning chain at DEBUG level
            logger.debug(
                "llm_reasoning_chain",
                component="validator",
                domain=self.domain,
                action=action.action_string or str(action.action_type),
                is_valid=result.is_valid,
                reasoning=result.reasoning,
                confidence=result.confidence
            )

            # Mark action with validation result
            validated_action = action.model_copy(update={
                "validated": result.is_valid,
                "validation_result": result
            })

            # Update statistics
            if result.is_valid:
                self.validation_count += 1
            else:
                self.rejection_count += 1

            # In permissive mode, include all actions regardless of validation
            # In strict mode, only include valid actions
            if self.permissive or result.is_valid:
                validated_actions.append(validated_action)

        return validated_actions

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Synchronous validate_action (not supported for async LLM validator).

        This method is required by BaseValidator but not used by LLMValidator.
        Use validate_actions instead.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            Always raises NotImplementedError

        Raises:
            NotImplementedError: LLMValidator only supports async validate_actions
        """
        raise NotImplementedError(
            "LLMValidator only supports async validate_actions. "
            "Use 'await validator.validate_actions([action], state)' instead."
        )