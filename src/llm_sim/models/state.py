"""State models for the simulation."""

from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field

from llm_sim.models.llm_models import LLMReasoningChain


class AgentState(BaseModel):
    """State of an individual agent."""

    model_config = ConfigDict(frozen=True)

    name: str
    economic_strength: float


class GlobalState(BaseModel):
    """Global simulation state."""

    model_config = ConfigDict(frozen=True)

    interest_rate: float
    total_economic_value: float = 0.0  # Default for backward compatibility
    # Additional economic indicators
    gdp_growth: float = 0.0
    inflation: float = 0.0
    unemployment: float = 0.0


class SimulationState(BaseModel):
    """Complete simulation state."""

    model_config = ConfigDict(frozen=True)

    turn: int
    agents: Dict[str, AgentState]
    global_state: GlobalState
    reasoning_chains: List[LLMReasoningChain] = Field(default_factory=list)
