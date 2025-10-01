"""Configuration models for the simulation."""

from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator


class TerminationConditions(BaseModel):
    """Conditions for terminating the simulation."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None


class SimulationSettings(BaseModel):
    """Main simulation settings."""

    name: str
    max_turns: int
    termination: Optional[TerminationConditions] = None
    checkpoint_interval: Optional[int] = None

    @field_validator("max_turns")
    @classmethod
    def validate_max_turns(cls, v: int) -> int:
        """Validate max_turns is positive."""
        if v <= 0:
            raise ValueError("max_turns must be greater than 0")
        return v

    @field_validator("checkpoint_interval")
    @classmethod
    def validate_checkpoint_interval(cls, v: Optional[int]) -> Optional[int]:
        """Validate checkpoint_interval is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("checkpoint_interval must be greater than 0")
        return v


class EngineConfig(BaseModel):
    """Engine configuration."""

    type: str
    interest_rate: Optional[float] = 0.05

    @field_validator("interest_rate")
    @classmethod
    def validate_interest_rate(cls, v: Optional[float]) -> Optional[float]:
        """Validate interest rate is within bounds."""
        if v is not None and not -1.0 <= v <= 1.0:
            raise ValueError("interest_rate must be between -1.0 and 1.0")
        return v


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    type: str
    initial_economic_strength: float


class ValidatorConfig(BaseModel):
    """Validator configuration."""

    type: str
    domain: Optional[str] = None  # Required for llm_validator (e.g., "economic")
    permissive: bool = True  # Per spec FR-005a


class LLMConfig(BaseModel):
    """LLM client configuration."""

    model: str = "gemma:3"
    host: str = "http://localhost:11434"
    timeout: float = 60.0
    max_retries: int = 1  # Per spec FR-014
    temperature: float = 0.7
    stream: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"


class SimulationConfig(BaseModel):
    """Complete simulation configuration."""

    simulation: SimulationSettings
    engine: EngineConfig
    agents: List[AgentConfig]
    validator: ValidatorConfig
    logging: Optional[LoggingConfig] = None  # Optional for backward compatibility
    llm: Optional[LLMConfig] = None  # Optional for backward compatibility

    @model_validator(mode="after")
    def validate_unique_agent_names(self) -> "SimulationConfig":
        """Validate that all agent names are unique."""
        agent_names = [agent.name for agent in self.agents]
        if len(agent_names) != len(set(agent_names)):
            raise ValueError("All agent names must be unique, found duplicates")
        return self
