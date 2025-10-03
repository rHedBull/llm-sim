"""Lifecycle management models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LifecycleOperation(str, Enum):
    """Lifecycle operation types."""

    ADD_AGENT = "add_agent"
    REMOVE_AGENT = "remove_agent"
    PAUSE_AGENT = "pause_agent"
    RESUME_AGENT = "resume_agent"


class LifecycleAction(BaseModel):
    """Represents an agent-initiated request to modify the agent population."""

    operation: LifecycleOperation
    initiating_agent: Optional[str] = None  # None for external operations
    target_agent_name: str
    initial_state: Optional[Dict[str, Any]] = None  # For ADD_AGENT only
    auto_resume_turns: Optional[int] = None  # For PAUSE_AGENT only

    def model_post_init(self, __context: Any) -> None:
        """Validate operation-specific fields."""
        if self.operation == LifecycleOperation.ADD_AGENT and self.initial_state is None:
            raise ValueError("initial_state must be provided for ADD_AGENT operation")


class ValidationResult(BaseModel):
    """Represents the outcome of lifecycle action validation."""

    valid: bool
    reason: Optional[str] = None  # Explanation if validation fails
    warnings: List[str] = Field(default_factory=list)  # Non-critical issues
