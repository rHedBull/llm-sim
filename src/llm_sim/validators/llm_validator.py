"""Abstract base class for LLM-enabled validators."""

from abc import abstractmethod
from datetime import datetime
from typing import List

import structlog

from llm_sim.validators.base import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.llm_models import ValidationResult
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

logger = structlog.get_logger()


class LLMValidator(BaseValidator):
    """Abstract base class for validators that use LLM reasoning.
    
    This class provides the LLM infrastructure while requiring
    subclasses to implement domain-specific validation prompts
    and domain descriptions.
    """

    def __init__(self, llm_client: LLMClient, domain: str, permissive: bool = True):
        """Initialize LLM-enabled validator.

        Args:
            llm_client: LLM client for reasoning
            domain: Domain name (e.g., "economic", "military")
            permissive: Whether to use permissive validation (accept boundary cases)
        """
        super().__init__()
        self.llm_client = llm_client
        self.domain = domain
        self.permissive = permissive

    @abstractmethod
    def _construct_validation_prompt(self, action: Action) -> str:
        """Construct domain-specific validation prompt.
        
        Args:
            action: Action to validate
            
        Returns:
            Prompt string to send to LLM
        """
        pass

    @abstractmethod
    def _get_domain_description(self) -> str:
        """Get description of domain boundaries.

        Returns:
            String describing what is/isn't in this domain
        """
        pass

    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Synchronous wrapper - not used in LLM validator.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            Always returns True (actual validation happens in validate_actions)
        """
        # LLM validator uses async validate_actions instead
        return True

    async def validate_actions(
        self, actions: List[Action], state: SimulationState
    ) -> List[Action]:
        """Validate actions using LLM reasoning.
        
        Args:
            actions: Actions to validate
            state: Current simulation state
            
        Returns:
            Same list of actions with validated field updated
        """
        validated_actions = []
        
        for action in actions:
            start_time = datetime.now()
            
            # Step 1: Construct validation prompt
            prompt = self._construct_validation_prompt(action)
            
            # Step 2: Call LLM with retry logic
            result = await self.llm_client.call_with_retry(
                prompt=prompt,
                response_model=ValidationResult
            )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Step 3: Log reasoning chain at DEBUG level
            logger.debug(
                "llm_reasoning_chain",
                component="validator",
                action=action.action_string,
                is_valid=result.is_valid,
                reasoning=result.reasoning,
                confidence=result.confidence,
                duration_ms=duration_ms
            )
            
            # Step 4: Mark action as validated or not
            if result.is_valid:
                validated_action = action.model_copy(
                    update={
                        "validated": True,
                        "validation_result": result,
                        "validation_timestamp": datetime.now()
                    }
                )
            else:
                validated_action = action.model_copy(
                    update={
                        "validated": False,
                        "validation_result": result
                    }
                )
            
            validated_actions.append(validated_action)
        
        return validated_actions
