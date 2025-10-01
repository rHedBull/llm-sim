"""State models for the simulation."""

from typing import Any, Dict, List, Type, get_args
from pydantic import BaseModel, ConfigDict, Field, create_model

from llm_sim.models.llm_models import LLMReasoningChain
from llm_sim.models.config import VariableDefinition


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


def create_agent_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]:
    """Generate AgentState model from variable definitions.

    Args:
        var_defs: Dictionary mapping variable names to their definitions

    Returns:
        Dynamically created Pydantic model class for AgentState
    """
    fields: Dict[str, Any] = {"name": (str, ...)}  # Required field

    for var_name, var_def in var_defs.items():
        if var_def.type == "float":
            field_args = {"default": var_def.default}
            if var_def.min is not None:
                field_args["ge"] = var_def.min
            if var_def.max is not None:
                field_args["le"] = var_def.max
            fields[var_name] = (float, Field(**field_args))

        elif var_def.type == "int":
            field_args = {"default": var_def.default}
            if var_def.min is not None:
                field_args["ge"] = int(var_def.min)
            if var_def.max is not None:
                field_args["le"] = int(var_def.max)
            fields[var_name] = (int, Field(**field_args))

        elif var_def.type == "bool":
            fields[var_name] = (bool, Field(default=var_def.default))

        elif var_def.type == "categorical":
            from typing import Literal

            # Create Literal type from values
            literal_type = Literal[tuple(var_def.values)]  # type: ignore
            fields[var_name] = (literal_type, Field(default=var_def.default))

    # Create the base model
    model = create_model(
        "AgentState", __config__=ConfigDict(frozen=True, arbitrary_types_allowed=True), **fields
    )

    # Override model_copy to include validation
    original_model_copy = model.model_copy

    def validated_model_copy(self, *, update: Dict[str, Any] | None = None, deep: bool = False):
        """model_copy that validates the updated fields."""
        # Get current data
        data = self.model_dump()
        # Apply updates
        if update:
            data.update(update)
        # Create new instance with validation
        return model(**data)

    model.model_copy = validated_model_copy  # type: ignore

    return model


def create_global_state_model(var_defs: Dict[str, VariableDefinition]) -> Type[BaseModel]:
    """Generate GlobalState model from variable definitions.

    Args:
        var_defs: Dictionary mapping variable names to their definitions

    Returns:
        Dynamically created Pydantic model class for GlobalState
    """
    fields: Dict[str, Any] = {}

    for var_name, var_def in var_defs.items():
        if var_def.type == "float":
            field_args = {"default": var_def.default}
            if var_def.min is not None:
                field_args["ge"] = var_def.min
            if var_def.max is not None:
                field_args["le"] = var_def.max
            fields[var_name] = (float, Field(**field_args))

        elif var_def.type == "int":
            field_args = {"default": var_def.default}
            if var_def.min is not None:
                field_args["ge"] = int(var_def.min)
            if var_def.max is not None:
                field_args["le"] = int(var_def.max)
            fields[var_name] = (int, Field(**field_args))

        elif var_def.type == "bool":
            fields[var_name] = (bool, Field(default=var_def.default))

        elif var_def.type == "categorical":
            from typing import Literal

            # Create Literal type from values
            literal_type = Literal[tuple(var_def.values)]  # type: ignore
            fields[var_name] = (literal_type, Field(default=var_def.default))

    # Create the base model
    model = create_model(
        "GlobalState", __config__=ConfigDict(frozen=True, arbitrary_types_allowed=True), **fields
    )

    # Override model_copy to include validation
    original_model_copy = model.model_copy

    def validated_model_copy(self, *, update: Dict[str, Any] | None = None, deep: bool = False):
        """model_copy that validates the updated fields."""
        # Get current data
        data = self.model_dump()
        # Apply updates
        if update:
            data.update(update)
        # Create new instance with validation
        return model(**data)

    model.model_copy = validated_model_copy  # type: ignore

    return model
