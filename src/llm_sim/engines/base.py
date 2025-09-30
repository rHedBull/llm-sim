"""Base engine interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState


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
        new_state = self.apply_actions(actions)
        new_state = self.apply_engine_rules(new_state)

        self._state = new_state
        self._turn_counter += 1

        return new_state
