"""Lifecycle operation validation."""

from typing import Optional

from llm_sim.models.lifecycle import ValidationResult
from llm_sim.models.state import SimulationState


class LifecycleValidator:
    """Validates lifecycle operations against constraints and current state."""

    MAX_AGENTS = 25

    def validate_add(self, name: str, state: SimulationState) -> ValidationResult:
        """Validate agent addition.

        Args:
            name: Proposed agent name
            state: Current simulation state

        Returns:
            ValidationResult indicating if addition is valid
        """
        # Check max agent count
        if len(state.agents) >= self.MAX_AGENTS:
            return ValidationResult(
                valid=False, reason=f"Maximum agent count ({self.MAX_AGENTS}) reached. Cannot add '{name}'."
            )

        # Name collision will be handled by manager (auto-rename)
        # So this validation always passes if count < max
        return ValidationResult(valid=True)

    def validate_remove(self, name: str, state: SimulationState) -> ValidationResult:
        """Validate agent removal.

        Args:
            name: Agent name to remove
            state: Current simulation state

        Returns:
            ValidationResult indicating if removal is valid
        """
        # Check agent exists
        if name not in state.agents:
            return ValidationResult(valid=False, reason=f"Agent '{name}' does not exist. Cannot remove.")

        # Allow removing last agent (simulation can have 0 agents)
        return ValidationResult(valid=True)

    def validate_pause(
        self, name: str, auto_resume: Optional[int], state: SimulationState
    ) -> ValidationResult:
        """Validate agent pause.

        Args:
            name: Agent name to pause
            auto_resume: Optional turns until auto-resume
            state: Current simulation state

        Returns:
            ValidationResult indicating if pause is valid
        """
        # Check agent exists
        if name not in state.agents:
            return ValidationResult(valid=False, reason=f"Agent '{name}' does not exist. Cannot pause.")

        # Check agent not already paused
        if name in state.paused_agents:
            return ValidationResult(valid=False, reason=f"Agent '{name}' is already paused. Cannot pause again.")

        # Check auto_resume is valid (None or positive integer)
        if auto_resume is not None and auto_resume <= 0:
            return ValidationResult(
                valid=False, reason=f"auto_resume_turns must be positive integer or None. Got: {auto_resume}"
            )

        return ValidationResult(valid=True)

    def validate_resume(self, name: str, state: SimulationState) -> ValidationResult:
        """Validate agent resume.

        Args:
            name: Agent name to resume
            state: Current simulation state

        Returns:
            ValidationResult indicating if resume is valid
        """
        # Check agent exists
        if name not in state.agents:
            return ValidationResult(valid=False, reason=f"Agent '{name}' does not exist. Cannot resume.")

        # Check agent is paused
        if name not in state.paused_agents:
            return ValidationResult(valid=False, reason=f"Agent '{name}' is not paused. Cannot resume.")

        return ValidationResult(valid=True)
