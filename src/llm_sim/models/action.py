"""Action models for the simulation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel

from llm_sim.models.llm_models import PolicyDecision, ValidationResult


class ActionType(str, Enum):
    """Types of actions agents can take."""

    GROW = "grow"
    MAINTAIN = "maintain"
    DECLINE = "decline"


class Action(BaseModel):
    """Action taken by an agent."""

    agent_name: str
    # Legacy fields (backward compatibility)
    action_type: Optional[ActionType] = None
    parameters: Optional[Dict[str, Any]] = None
    # New LLM fields
    action_string: Optional[str] = None  # Replaces action_type for LLM mode
    policy_decision: Optional[PolicyDecision] = None  # LLM-generated decision
    validation_result: Optional[ValidationResult] = None  # Populated by validator
    reasoning_chain_id: Optional[str] = None  # Reference to LLMReasoningChain
    # Validation status
    validated: bool = False
    validation_timestamp: Optional[datetime] = None

    def mark_validated(self) -> "Action":
        """Mark this action as validated.

        Returns:
            New Action instance marked as validated
        """
        return self.model_copy(update={"validated": True, "validation_timestamp": datetime.now()})
