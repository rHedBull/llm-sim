"""Abstract base class for LLM-enabled agents."""

from abc import abstractmethod
from datetime import datetime

import structlog

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action, LLMAction
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

logger = structlog.get_logger()


class LLMAgent(BaseAgent):
    """Abstract base class for agents that use LLM reasoning.

    This class provides the LLM infrastructure while requiring
    subclasses to implement domain-specific prompt construction
    and decision validation.
    """

    def __init__(self, name: str, llm_client: LLMClient):
        """Initialize LLM-enabled agent.

        Args:
            name: Agent name
            llm_client: LLM client for reasoning
        """
        super().__init__(name=name)
        self.llm_client = llm_client

    @abstractmethod
    def _construct_prompt(self, state: SimulationState) -> str:
        """Construct domain-specific prompt for LLM.

        Args:
            state: Current simulation state

        Returns:
            Prompt string to send to LLM
        """
        pass

    @abstractmethod
    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Validate that decision is within domain boundaries.

        Args:
            decision: LLM-generated policy decision

        Returns:
            True if decision is valid for this domain
        """
        pass

    async def decide_action(self, state: SimulationState) -> Action:
        """Generate action using LLM reasoning.

        Args:
            state: Current simulation state

        Returns:
            Action with policy decision

        Raises:
            LLMFailureException: If LLM fails after retry
        """
        start_time = datetime.now()

        # Step 1: Construct domain-specific prompt
        prompt = self._construct_prompt(state)

        # Step 2: Call LLM with retry logic
        decision = await self.llm_client.call_with_retry(
            prompt=prompt,
            response_model=PolicyDecision
        )

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Step 3: Validate decision
        if not self._validate_decision(decision):
            logger.warning(
                "agent_decision_invalid",
                agent=self.name,
                action=decision.action,
                reason="Failed domain validation"
            )
            # Still create action but mark as potentially problematic

        # Step 4: Log reasoning chain at DEBUG level
        logger.debug(
            "llm_reasoning_chain",
            component="agent",
            agent_name=self.name,
            reasoning=decision.reasoning,
            confidence=decision.confidence,
            duration_ms=duration_ms
        )

        # Step 5: Create LLMAction with policy decision
        action = LLMAction(
            agent_name=self.name,
            action_name=decision.action,
            action_string=decision.action,
            policy_decision=decision,
            parameters=getattr(decision, 'parameters', None),
            validated=False  # Will be set by validator
        )

        return action
