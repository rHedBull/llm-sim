"""Base validator interface."""

from abc import ABC, abstractmethod
from typing import Dict, List

from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class BaseValidator(ABC):
    """Abstract base class for action validators."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.validation_count: int = 0
        self.rejection_count: int = 0

    @abstractmethod
    def validate_action(self, action: Action, state: SimulationState) -> bool:
        """Validate single action against current state.

        Args:
            action: Action to validate
            state: Current simulation state

        Returns:
            True if action is valid, False otherwise
        """
        pass

    def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        """Validate and mark all actions.

        Args:
            actions: List of actions to validate
            state: Current simulation state

        Returns:
            List of validated actions (may be subset of input)
        """
        validated: List[Action] = []

        for action in actions:
            if self.validate_action(action, state):
                validated.append(action.mark_validated())
                self.validation_count += 1
            else:
                self.rejection_count += 1

        return validated

    def get_stats(self) -> Dict[str, float]:
        """Get validation statistics.

        Returns:
            Dictionary with validation stats
        """
        total = self.validation_count + self.rejection_count
        acceptance_rate = self.validation_count / total if total > 0 else 0.0

        return {
            "total_validated": float(self.validation_count),
            "total_rejected": float(self.rejection_count),
            "acceptance_rate": acceptance_rate,
        }
