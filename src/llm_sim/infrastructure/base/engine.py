"""Base engine interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState

if TYPE_CHECKING:
    from llm_sim.infrastructure.events import EventWriter


class BaseEngine(ABC):
    """Abstract base class for simulation engines."""

    def __init__(self, config: SimulationConfig) -> None:
        """Initialize engine with configuration.

        Args:
            config: Simulation configuration
        """
        self.config = config
        self._state: Optional[SimulationState] = None
        self._turn_counter: int = 0
        self._event_writer: Optional["EventWriter"] = None

    @abstractmethod
    def initialize_state(self) -> SimulationState:
        """Create initial simulation state from configuration.

        Returns:
            Initial SimulationState object
        """
        pass

    @abstractmethod
    def apply_actions(self, actions: List[Action]) -> SimulationState:
        """Apply validated actions to current state.

        Args:
            actions: List of validated actions from agents

        Returns:
            New SimulationState after applying actions
        """
        pass

    @abstractmethod
    def apply_engine_rules(self, state: SimulationState) -> SimulationState:
        """Apply engine-specific rules (e.g., interest growth).

        Args:
            state: Current simulation state

        Returns:
            New SimulationState after applying engine rules
        """
        pass

    @abstractmethod
    def check_termination(self, state: SimulationState) -> bool:
        """Check if simulation should terminate.

        Args:
            state: Current simulation state

        Returns:
            True if simulation should end, False otherwise
        """
        pass

    def set_event_writer(self, event_writer: Optional["EventWriter"]) -> None:
        """Set event writer for event emission.

        Args:
            event_writer: EventWriter instance or None
        """
        self._event_writer = event_writer

    def get_current_state(self) -> SimulationState:
        """Get current simulation state.

        Returns:
            Current SimulationState

        Raises:
            RuntimeError: If state not initialized
        """
        if self._state is None:
            raise RuntimeError("Engine state not initialized")
        return self._state

    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute one simulation turn.

        Args:
            actions: Validated actions from all agents

        Returns:
            New state after turn execution
        """
        # Emit ACTION events if event writer is available
        if self._event_writer and self._state:
            from llm_sim.infrastructure.events.builder import create_action_event

            for action in actions:
                if action.validated:  # Only emit for validated actions
                    event = create_action_event(
                        simulation_id=self._event_writer.simulation_id,
                        turn_number=self._state.turn + 1,
                        agent_id=action.agent_name,
                        action_type=action.action_name,
                        action_payload=action.params or {},
                        description=f"{action.agent_name} performed {action.action_name}"
                    )
                    self._event_writer.emit(event)

        new_state = self.apply_actions(actions)
        new_state = self.apply_engine_rules(new_state)

        self._state = new_state
        self._turn_counter += 1

        return new_state
