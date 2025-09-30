"""LLM-specific Pydantic models for reasoning-based simulations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LLMReasoningChain(BaseModel):
    """Captures the full reasoning output from an LLM call for auditability and debugging."""

    component: str = Field(..., description="Component that made the LLM call")
    agent_name: Optional[str] = Field(None, description="Name of agent if component is 'agent'")
    prompt: str = Field(..., min_length=1, description="Full prompt sent to LLM")
    response: str = Field(..., min_length=1, description="Raw LLM response")
    reasoning: str = Field(..., min_length=1, description="Extracted reasoning explanation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the LLM call was made")
    duration_ms: int = Field(..., ge=0, description="How long the LLM call took")
    model: str = Field(..., description="LLM model used (e.g., 'gemma:3')")
    retry_count: int = Field(..., ge=0, le=1, description="Number of retries (0 or 1)")

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        """Validate component is one of: agent, validator, engine."""
        if v not in ["agent", "validator", "engine"]:
            raise ValueError("component must be one of: agent, validator, engine")
        return v

    class Config:
        """Pydantic config."""
        frozen = True  # Immutable for audit trail integrity


class PolicyDecision(BaseModel):
    """Represents an agent's LLM-generated policy decision."""

    action: str = Field(..., min_length=1, max_length=500, description="Specific policy action description")
    reasoning: str = Field(..., min_length=10, max_length=2000, description="Step-by-step LLM explanation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM's confidence in the decision")

    @field_validator("action")
    @classmethod
    def validate_action_no_newlines(cls, v: str) -> str:
        """Ensure action is single-line (no newlines)."""
        if "\n" in v:
            raise ValueError("action must not contain newlines (single-line action description)")
        return v

    class Config:
        """Pydantic config."""
        frozen = True  # Immutable once generated


class ValidationResult(BaseModel):
    """Represents the Validator's LLM-based domain validation decision."""

    is_valid: bool = Field(..., description="Whether the action is valid for the simulation domain")
    reasoning: str = Field(..., min_length=10, max_length=2000, description="Step-by-step LLM explanation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM's confidence in the validation")
    action_evaluated: str = Field(..., description="The action string that was validated (for traceability)")

    class Config:
        """Pydantic config."""
        frozen = True  # Immutable once generated


class StateUpdateDecision(BaseModel):
    """Represents the Engine's LLM-based decision on how to update simulation state."""

    new_interest_rate: float = Field(..., description="The calculated interest rate after applying the action")
    reasoning: str = Field(..., min_length=10, max_length=2000, description="Step-by-step LLM explanation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM's confidence in the calculation")
    action_applied: str = Field(..., description="The validated action that was applied (for traceability)")

    class Config:
        """Pydantic config."""
        frozen = True  # Immutable once generated