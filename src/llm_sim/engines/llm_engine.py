"""Abstract base class for LLM-enabled engines."""

from abc import abstractmethod
from datetime import datetime
from typing import List

import structlog

from llm_sim.engines.base import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.llm_models import StateUpdateDecision, LLMReasoningChain
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient

logger = structlog.get_logger()


class LLMEngine(BaseEngine):
    """Abstract base class for engines that use LLM reasoning.
    
    This class provides the LLM infrastructure while requiring
    subclasses to implement domain-specific state update logic.
    """

    def __init__(self, config, llm_client: LLMClient):
        """Initialize LLM-enabled engine.
        
        Args:
            config: Engine configuration
            llm_client: LLM client for reasoning
        """
        super().__init__(config=config)
        self.llm_client = llm_client
        self.current_state = None

    @abstractmethod
    def _construct_state_update_prompt(
        self, action: Action, state
    ) -> str:
        """Construct domain-specific state update prompt.
        
        Args:
            action: Validated action to apply
            state: Current global state
            
        Returns:
            Prompt string to send to LLM
        """
        pass

    @abstractmethod
    def _apply_state_update(
        self, decision: StateUpdateDecision, state: SimulationState
    ) -> SimulationState:
        """Apply LLM decision to create new state.

        Args:
            decision: LLM-generated state update decision
            state: Current simulation state

        Returns:
            New simulation state with updates applied
        """
        pass

    # Implement BaseEngine abstract methods with stubs
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state (must be overridden by concrete class)."""
        raise NotImplementedError("Concrete engine must implement initialize_state")

    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply actions (handled by run_turn in LLM engines)."""
        return self.current_state

    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine rules (handled by LLM in LLM engines)."""
        return state

    def check_termination(self, state: SimulationState) -> bool:
        """Check termination (must be overridden by concrete class)."""
        return False

    async def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        """Process validated actions and update state using LLM reasoning.
        
        Args:
            validated_actions: Actions from agents (some may be unvalidated)
            
        Returns:
            New simulation state after applying actions
        """
        reasoning_chains = []
        working_state = self.current_state
        
        # Filter to only validated actions
        for action in validated_actions:
            if not action.validated:
                # Skip unvalidated actions with INFO log (per spec FR-008)
                logger.info(
                    "action_skipped",
                    agent=action.agent_name,
                    action=action.action_string,
                    reason="unvalidated"
                )
                logger.info(
                    f"SKIPPED Agent [{action.agent_name}] due to unvalidated Action"
                )
                continue
            
            # Process validated action
            start_time = datetime.now()
            
            # Step 1: Construct state update prompt
            prompt = self._construct_state_update_prompt(
                action, working_state.global_state
            )
            
            # Step 2: Call LLM with retry logic
            decision = await self.llm_client.call_with_retry(
                prompt=prompt,
                response_model=StateUpdateDecision
            )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Step 3: Log reasoning chain at DEBUG level
            logger.debug(
                "llm_reasoning_chain",
                component="engine",
                action=action.action_string,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                duration_ms=duration_ms
            )
            
            # Step 4: Create reasoning chain record
            chain = LLMReasoningChain(
                component="engine",
                agent_name=action.agent_name,
                prompt=prompt,
                response=str(decision),
                reasoning=decision.reasoning,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                model=self.llm_client.config.model,
                retry_count=0  # TODO: Track actual retry count
            )
            reasoning_chains.append(chain)
            
            # Step 5: Apply state update
            working_state = self._apply_state_update(decision, working_state)
        
        # Attach reasoning chains to new state
        new_state = working_state.model_copy(
            update={"reasoning_chains": reasoning_chains}
        )
        
        self.current_state = new_state
        return new_state
