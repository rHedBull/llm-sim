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
    termination: TerminationConditions

    @field_validator("max_turns")
    @classmethod
    def validate_max_turns(cls, v: int) -> int:
        """Validate max_turns is positive."""
        if v <= 0:
            raise ValueError("max_turns must be greater than 0")
        return v


class EngineConfig(BaseModel):
    """Engine configuration."""

    type: str
    interest_rate: float

    @field_validator("interest_rate")
    @classmethod
    def validate_interest_rate(cls, v: float) -> float:
        """Validate interest rate is within bounds."""
        if not -1.0 <= v <= 1.0:
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
    logging: LoggingConfig

    @model_validator(mode="after")
    def validate_unique_agent_names(self) -> "SimulationConfig":
        """Validate that all agent names are unique."""
        agent_names = [agent.name for agent in self.agents]
        if len(agent_names) != len(set(agent_names)):
            raise ValueError("All agent names must be unique, found duplicates")
        return self
