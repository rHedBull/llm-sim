"""LLM-powered agent abstract base class."""

from abc import ABC, abstractmethod

import structlog

from llm_sim.agents.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.llm_models import PolicyDecision
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

logger = structlog.get_logger()


class LLMAgent(BaseAgent, ABC):
    """Abstract base class for LLM-powered simulation agents.

    Extends BaseAgent with LLM infrastructure for reasoning-based decision making.
    Subclasses must implement domain-specific prompt construction and validation.
    """

    def __init__(self, name: str, llm_client: LLMClient) -> None:
        """Initialize LLM agent with client.

        Args:
            name: Unique identifier for this agent
            llm_client: Client for LLM interactions
        """
        super().__init__(name)
        self.llm_client = llm_client

    @abstractmethod
    def _construct_prompt(self, state: SimulationState) -> str:
        """Construct domain-specific prompt for LLM.

        Args:
            state: Current simulation state

        Returns:
            Full prompt string to send to LLM
        """
        pass

    @abstractmethod
    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Validate domain-specific policy decision.

        Args:
            decision: LLM-generated policy decision

        Returns:
            True if decision is acceptable for this domain
        """
        pass

    async def decide_action(self, state: SimulationState) -> Action:
        """Decide on action using LLM reasoning.

        Args:
            state: Current simulation state

        Returns:
            Action with LLM-generated policy decision

        Raises:
            LLMFailureException: If LLM call fails after retries
        """
        # Construct domain-specific prompt
        prompt = self._construct_prompt(state)

        # Call LLM with retry logic
        decision = await self.llm_client.call_with_retry(
            prompt=prompt,
            response_model=PolicyDecision,
            component="agent"
        )

        # Log reasoning chain at DEBUG level
        logger.debug(
            "llm_reasoning_chain",
            component="agent",
            agent_name=self.name,
            reasoning=decision.reasoning,
            confidence=decision.confidence,
            action=decision.action
        )

        # Validate decision
        if not self._validate_decision(decision):
            logger.warning(
                "invalid_decision",
                component="agent",
                agent_name=self.name,
                action=decision.action,
                reasoning=decision.reasoning
            )

        # Create and return Action
        return Action(
            agent_name=self.name,
            action_string=decision.action,
            policy_decision=decision,
            validated=False
        )