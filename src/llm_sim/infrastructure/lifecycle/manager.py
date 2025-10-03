"""Lifecycle management coordinator."""

from typing import Any, Dict, List, Optional
import structlog

from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker
from llm_sim.infrastructure.lifecycle.validator import LifecycleValidator
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.state import SimulationState


logger = structlog.get_logger()


class LifecycleManager:
    """Coordinates all agent lifecycle operations."""

    def __init__(
        self, validator: Optional[LifecycleValidator] = None, pause_tracker: Optional[PauseTracker] = None
    ):
        """Initialize lifecycle manager.

        Args:
            validator: Lifecycle validator (creates new if None)
            pause_tracker: Pause tracker (creates new if None)
        """
        self.validator = validator or LifecycleValidator()
        self.pause_tracker = pause_tracker or PauseTracker()
        self.logger = logger.bind(component="lifecycle_manager")

    def add_agent(
        self, name: str, agent: BaseAgent, initial_state: Dict[str, Any], state: SimulationState
    ) -> str:
        """Add agent with collision resolution.

        Args:
            name: Proposed agent name
            agent: Agent instance
            initial_state: Initial state for agent
            state: Current simulation state

        Returns:
            Resolved agent name (may differ from input if collision)
        """
        # Validate
        validation = self.validator.validate_add(name, state)
        if not validation.valid:
            self.logger.warning(
                "lifecycle_validation_failed",
                operation="add_agent",
                agent_name=name,
                reason=validation.reason,
                turn=state.turn,
            )
            return name  # Return original name even though not added

        # Resolve name collision
        resolved_name = self._resolve_name_collision(name, state)

        # Add agent to state
        # Note: State is frozen, but we can modify mutable fields (dict, set)
        from llm_sim.models.state import create_agent_state_model

        # Get the agent state model class from existing agents or create minimal one
        if state.agents:
            # Use same model as existing agents
            AgentState = type(next(iter(state.agents.values())))
        else:
            # Create minimal agent state model
            AgentState = create_agent_state_model({})

        # Create agent state
        agent_state = AgentState(name=resolved_name, **initial_state)

        # Add to agents dict (state.agents is mutable dict within frozen model)
        state.agents[resolved_name] = agent_state

        self.logger.info(
            "lifecycle_operation",
            operation="add_agent",
            agent_name=name,
            resolved_name=resolved_name,
            turn=state.turn,
        )

        return resolved_name

    def remove_agent(self, name: str, state: SimulationState) -> bool:
        """Remove agent from simulation.

        Args:
            name: Agent name to remove
            state: Current simulation state

        Returns:
            True if agent was removed, False if validation failed
        """
        # Validate
        validation = self.validator.validate_remove(name, state)
        if not validation.valid:
            self.logger.warning(
                "lifecycle_validation_failed",
                operation="remove_agent",
                agent_name=name,
                reason=validation.reason,
                turn=state.turn,
            )
            return False

        # Remove from agents dict
        del state.agents[name]

        # Remove from pause tracking if present
        self.pause_tracker.resume(name)  # This removes from both paused_agents and auto_resume

        self.logger.info("lifecycle_operation", operation="remove_agent", agent_name=name, turn=state.turn)

        return True

    def pause_agent(self, name: str, auto_resume_turns: Optional[int], state: SimulationState) -> bool:
        """Pause an agent.

        Args:
            name: Agent name to pause
            auto_resume_turns: Optional turns until auto-resume
            state: Current simulation state

        Returns:
            True if agent was paused, False if validation failed
        """
        # Validate
        validation = self.validator.validate_pause(name, auto_resume_turns, state)
        if not validation.valid:
            self.logger.warning(
                "lifecycle_validation_failed",
                operation="pause_agent",
                agent_name=name,
                reason=validation.reason,
                turn=state.turn,
            )
            return False

        # Pause agent
        self.pause_tracker.pause(name, auto_resume_turns)

        # Update state paused_agents set
        state.paused_agents.add(name)
        if auto_resume_turns is not None:
            state.auto_resume[name] = auto_resume_turns

        self.logger.info(
            "lifecycle_operation",
            operation="pause_agent",
            agent_name=name,
            auto_resume_turns=auto_resume_turns,
            turn=state.turn,
        )

        return True

    def resume_agent(self, name: str, state: SimulationState) -> bool:
        """Resume a paused agent.

        Args:
            name: Agent name to resume
            state: Current simulation state

        Returns:
            True if agent was resumed, False if validation failed
        """
        # Validate
        validation = self.validator.validate_resume(name, state)
        if not validation.valid:
            self.logger.warning(
                "lifecycle_validation_failed",
                operation="resume_agent",
                agent_name=name,
                reason=validation.reason,
                turn=state.turn,
            )
            return False

        # Resume agent
        self.pause_tracker.resume(name)

        # Update state paused_agents set
        state.paused_agents.discard(name)
        state.auto_resume.pop(name, None)

        self.logger.info("lifecycle_operation", operation="resume_agent", agent_name=name, turn=state.turn)

        return True

    def get_active_agents(self, state: SimulationState) -> Dict[str, Any]:
        """Get dict of active (non-paused) agents.

        Args:
            state: Current simulation state

        Returns:
            Dict of agents excluding paused agents
        """
        return {name: agent for name, agent in state.agents.items() if name not in state.paused_agents}

    def process_auto_resume(self, state: SimulationState) -> List[str]:
        """Process auto-resume for one turn.

        Args:
            state: Current simulation state

        Returns:
            List of agent names that were auto-resumed
        """
        resumed = self.pause_tracker.tick_auto_resume()

        # Update state
        for name in resumed:
            state.paused_agents.discard(name)
            state.auto_resume.pop(name, None)

        if resumed:
            self.logger.info("auto_resume_processed", resumed_agents=resumed, turn=state.turn)

        return resumed

    def _resolve_name_collision(self, base_name: str, state: SimulationState) -> str:
        """Resolve name collision by appending numeric suffix.

        Args:
            base_name: Proposed agent name
            state: Current simulation state

        Returns:
            Unique agent name
        """
        if base_name not in state.agents:
            return base_name

        counter = 1
        while f"{base_name}_{counter}" in state.agents:
            counter += 1

        return f"{base_name}_{counter}"
