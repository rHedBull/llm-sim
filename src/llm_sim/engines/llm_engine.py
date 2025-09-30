"""LLM-based engine abstract base class."""

from abc import abstractmethod
from typing import List

import structlog

from llm_sim.engines.base import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.llm_models import LLMReasoningChain, StateUpdateDecision
from llm_sim.models.state import GlobalState, SimulationState
from llm_sim.utils.llm_client import LLMClient

logger = structlog.get_logger()


class LLMEngine(BaseEngine):
    """Abstract base class for LLM-based simulation engines.

    Adds LLM state reasoning infrastructure to BaseEngine.
    Provides common LLM client management, state update prompt framework,
    and reasoning chain aggregation.
    """

    def __init__(self, config: SimulationConfig, llm_client: LLMClient) -> None:
        """Initialize LLM engine with configuration and LLM client.

        Args:
            config: Simulation configuration
            llm_client: LLM client for making LLM calls with retry logic
        """
        super().__init__(config)
        self.llm_client = llm_client
        self.current_state: SimulationState = None

    @abstractmethod
    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        """Construct domain-specific state update prompt.

        Args:
            action: Validated action to apply
            state: Current global state

        Returns:
            Full prompt string for LLM state reasoning
        """
        pass

    @abstractmethod
    def _apply_state_update(
        self,
        decision: StateUpdateDecision,
        state: SimulationState
    ) -> SimulationState:
        """Apply domain-specific state update.

        Args:
            decision: LLM-generated state update decision
            state: Current simulation state

        Returns:
            New SimulationState with updates applied
        """
        pass

    async def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        """Execute one simulation turn using LLM reasoning.

        Processes validated actions using LLM reasoning to compute new simulation state.

        Args:
            validated_actions: List of actions (may include unvalidated actions)

        Returns:
            New SimulationState with updated state and reasoning chains

        Raises:
            LLMFailureException: If LLM call fails after retries
        """
        # Filter to validated actions only
        valid_actions = []
        for action in validated_actions:
            if action.validated:
                valid_actions.append(action)
            else:
                # Log INFO message for skipped actions (per spec FR-008)
                logger.info(
                    f"SKIPPED Agent [{action.agent_name}] due to unvalidated Action",
                    agent=action.agent_name,
                    action=action.action_string
                )

        # Accumulate reasoning chains
        reasoning_chains: List[LLMReasoningChain] = []

        # Process each validated action
        current_state = self.current_state
        for action in valid_actions:
            # Construct state update prompt
            prompt = self._construct_state_update_prompt(
                action,
                current_state.global_state
            )

            # Call LLM with retry logic
            decision = await self.llm_client.call_with_retry(
                prompt=prompt,
                response_model=StateUpdateDecision,
                component="engine"
            )

            # Log reasoning at DEBUG level (per spec FR-017)
            logger.debug(
                "llm_reasoning_chain",
                component="engine",
                agent=action.agent_name,
                action=action.action_string,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                new_interest_rate=decision.new_interest_rate
            )

            # Apply state update
            current_state = self._apply_state_update(decision, current_state)

        # Attach reasoning chains to new state
        # Note: The reasoning chains are populated by the LLMClient's logging
        # For now, we'll use the reasoning_chains from the current state
        # In a full implementation, we'd capture the LLMReasoningChain objects
        # from the LLMClient calls
        new_state = current_state.model_copy(
            update={"reasoning_chains": reasoning_chains}
        )

        # Update internal state
        self.current_state = new_state

        return new_state

    # Implement abstract methods from BaseEngine
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state from configuration.

        Returns:
            Initial SimulationState object
        """
        # This will be implemented by concrete subclasses
        raise NotImplementedError("Subclasses must implement initialize_state")

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions to current state.

        This is replaced by run_turn in LLM-based engines.

        Args:
            actions: List of validated actions from agents

        Returns:
            New SimulationState after applying actions
        """
        raise NotImplementedError("Use run_turn instead for LLM-based engines")

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine-specific rules.

        Args:
            state: Current simulation state

        Returns:
            New SimulationState after applying engine rules
        """
        # For LLM engines, rules are applied via LLM reasoning
        # This may be implemented by subclasses if needed
        return state

    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate.

        Args:
            state: Current simulation state

        Returns:
            True if simulation should end, False otherwise
        """
        # Default implementation - subclasses can override
        return False