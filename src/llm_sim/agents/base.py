"""Base agent interface."""

from abc import ABC, abstractmethod
from typing import Optional

from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class BaseAgent(ABC):
    """Abstract base class for simulation agents."""

    def __init__(self, name: str) -> None:
        """Initialize agent with unique name.

        Args:
            name: Unique identifier for this agent
        """
        self.name = name
        self._current_state: Optional[SimulationState] = None

    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide on action based on current state.

        Args:
            state: Current simulation state

        Returns:
            Action to be taken this turn
        """
        pass

    def receive_state(self, state: SimulationState) -> None:
        """Receive state update from engine.

        Args:
            state: New simulation state
        """
        self._current_state = state

    def get_current_state(self) -> Optional[SimulationState]:
        """Get agent's view of current state.

        Returns:
            Current SimulationState or None if not set
        """
        return self._current_state
