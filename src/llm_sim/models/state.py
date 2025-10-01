"""State models for the simulation."""

from typing import Any, Dict, List, Type, get_args
from pydantic import BaseModel, ConfigDict, Field, create_model, field_serializer

from llm_sim.models.llm_models import LLMReasoningChain
from llm_sim.models.config import VariableDefinition


# NOTE: AgentState and GlobalState are now created dynamically using factory functions
# create_agent_state_model() and create_global_state_model() below.
# The old hardcoded classes have been removed to support configuration-driven variables.


class SimulationState(BaseModel):
    """Complete simulation state.

    Note: agents and global_state fields accept dynamically created models
    from create_agent_state_model() and create_global_state_model().
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    turn: int
    agents: Dict[str, BaseModel]  # Values are dynamically created AgentState instances
    global_state: BaseModel  # Dynamically created GlobalState instance
    reasoning_chains: List[LLMReasoningChain] = Field(default_factory=list)

    @field_serializer('agents')
    def serialize_agents(self, agents: Dict[str, BaseModel], _info):
        """Serialize agents dict properly."""
        return {name: agent.model_dump() for name, agent in agents.items()}

    @field_serializer('global_state')
    def serialize_global_state(self, global_state: BaseModel, _info):
        """Serialize global_state properly."""
        return global_state.model_dump()


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
