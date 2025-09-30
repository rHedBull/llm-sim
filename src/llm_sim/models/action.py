"""Action models for the simulation."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid

from llm_sim.models.llm_models import PolicyDecision, ValidationResult


class Action(BaseModel):
    """Base action taken by an agent.

    This is the simple, non-LLM action used by traditional agents.
    """

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    action_name: str  # Simple action identifier (e.g., "grow", "maintain", "decline")
    parameters: Optional[Dict[str, Any]] = None
    validated: bool = False
    validation_timestamp: Optional[datetime] = None

    def mark_validated(self) -> "Action":
        """Mark this action as validated.

        Returns:
            New Action instance marked as validated
        """
        return self.model_copy(update={"validated": True, "validation_timestamp": datetime.now()})


class LLMAction(Action):
    """LLM-enhanced action with reasoning and validation metadata.

    Extends base Action with LLM-specific fields for reasoning chains,
    policy decisions, and detailed validation results.
    """

    # LLM-specific fields
    action_string: Optional[str] = None  # Natural language action description
    policy_decision: Optional[PolicyDecision] = None  # Full LLM-generated decision with reasoning
    validation_result: Optional[ValidationResult] = None  # Detailed validation from LLM validator
    reasoning_chain_id: Optional[str] = None  # Reference to LLMReasoningChain in state
