"""State models for the simulation."""

from typing import Dict
from pydantic import BaseModel, ConfigDict


class AgentState(BaseModel):
    """State of an individual agent."""

    model_config = ConfigDict(frozen=True)

    name: str
    economic_strength: float


class GlobalState(BaseModel):
    """Global simulation state."""

    model_config = ConfigDict(frozen=True)

    interest_rate: float
    total_economic_value: float


class SimulationState(BaseModel):
    """Complete simulation state."""

    model_config = ConfigDict(frozen=True)

    turn: int
    agents: Dict[str, AgentState]
    global_state: GlobalState
