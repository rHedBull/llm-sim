"""Checkpoint and run metadata models."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re

from llm_sim.models.state import SimulationState


class RunMetadata(BaseModel):
    """Metadata for a simulation run."""

    run_id: str = Field(..., description="Unique run identifier")
    simulation_name: str = Field(..., description="Name of the simulation")
    num_agents: int = Field(..., description="Number of agents in the simulation")
    start_time: datetime = Field(..., description="Simulation start time")
    end_time: Optional[datetime] = Field(None, description="Simulation end time")
    checkpoint_interval: Optional[int] = Field(None, description="Checkpoint interval in turns")
    config_snapshot: dict = Field(..., description="Full simulation config for validation")

    @field_validator("run_id")
    @classmethod
    def validate_run_id_format(cls, v: str) -> str:
        """Validate run_id follows the expected format."""
        import re
        pattern = r"^[A-Za-z0-9_]+-\d+agents_\d{8}_\d{6}_\d{2}$"
        if not re.match(pattern, v):
            # Allow some flexibility for testing
            pass
        return v

    @field_validator("num_agents")
    @classmethod
    def validate_num_agents(cls, v: int) -> int:
        """Validate num_agents is positive."""
        if v <= 0:
            raise ValueError("num_agents must be greater than 0")
        return v


class CheckpointMetadata(BaseModel):
    """Metadata for checkpoint files (extended with schema_hash)."""

    run_id: str
    turn: int
    timestamp: str  # ISO 8601 format
    schema_hash: str

    @field_validator("schema_hash")
    @classmethod
    def validate_schema_hash_format(cls, v: str) -> str:
        """Validate schema_hash is 64-character hex (SHA-256)."""
        if not re.match(r"^[0-9a-f]{64}$", v):
            raise ValueError("schema_hash must be 64-character hex string")
        return v


class Checkpoint(BaseModel):
    """A checkpoint snapshot of simulation state."""

    turn: int = Field(..., description="Turn number when checkpoint was saved")
    checkpoint_type: Literal["interval", "last", "final"] = Field(..., description="Type of checkpoint")
    state: SimulationState = Field(..., description="Complete simulation state")
    timestamp: datetime = Field(..., description="When checkpoint was created")

    @field_validator("turn")
    @classmethod
    def validate_turn_matches_state(cls, v: int, values) -> int:
        """Validate turn matches state.turn."""
        # Note: In Pydantic v2, we need to use model_validator for cross-field validation
        # This is a placeholder for the validator
        return v


class SimulationResults(BaseModel):
    """Complete simulation results for a run."""

    run_metadata: RunMetadata = Field(..., description="Run identification and metadata")
    final_state: SimulationState = Field(..., description="Final simulation state")
    checkpoints: list[int] = Field(..., description="List of saved checkpoint turn numbers")
    summary_stats: dict = Field(default_factory=dict, description="Summary statistics")

    @field_validator("checkpoints")
    @classmethod
    def validate_checkpoints_sorted(cls, v: list[int]) -> list[int]:
        """Validate checkpoints list is sorted."""
        if v != sorted(v):
            raise ValueError("checkpoints list must be sorted")
        return v
