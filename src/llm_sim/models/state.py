"""State models for the simulation."""

from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Type
from pydantic import BaseModel, ConfigDict, Field, create_model, field_serializer, field_validator, model_validator

from llm_sim.models.llm_models import LLMReasoningChain
from llm_sim.models.config import VariableDefinition


# NOTE: AgentState and GlobalState are now created dynamically using factory functions
# create_agent_state_model() and create_global_state_model() below.
# The old hardcoded classes have been removed to support configuration-driven variables.


class LocationState(BaseModel):
    """State for a single location in spatial topology."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    id: str = Field(..., min_length=1, description="Unique location identifier")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Location attributes (resources, terrain, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (coordinates, geometry, etc.)"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Location id must be non-empty")
        return v.strip()


class ConnectionState(BaseModel):
    """State for a connection between locations."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    type: str = Field(..., min_length=1, description="Connection type")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connection attributes (speed, capacity, cost, etc.)"
    )
    bidirectional: bool = Field(
        default=True,
        description="Whether connection is bidirectional"
    )

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Connection type must be non-empty")
        return v.strip()


class NetworkState(BaseModel):
    """State for a network layer connecting locations."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    name: str = Field(..., min_length=1, description="Network identifier")
    edges: Set[Tuple[str, str]] = Field(
        default_factory=set,
        description="Set of (location_id, location_id) tuples"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Network-level attributes"
    )

    @field_serializer('edges')
    def serialize_edges(self, edges: Set[Tuple[str, str]], _info):
        """Serialize edges as sorted list for determinism."""
        return sorted([list(edge) for edge in edges])

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Network name must be non-empty")
        return v.strip()

    @field_validator('edges')
    @classmethod
    def validate_edges(cls, v: Set[Tuple[str, str]]) -> Set[Tuple[str, str]]:
        for edge in v:
            if len(edge) != 2:
                raise ValueError(f"Edge must be 2-tuple, got {len(edge)}")
            if not edge[0] or not edge[1]:
                raise ValueError(f"Edge locations must be non-empty: {edge}")
        return v


class SpatialState(BaseModel):
    """Complete spatial state for simulation."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=False)

    topology_type: Literal["grid", "hex_grid", "network", "regions"] = Field(
        ...,
        description="Type of spatial topology"
    )
    agent_positions: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps agent name to location ID"
    )
    locations: Dict[str, LocationState] = Field(
        default_factory=dict,
        description="Maps location ID to location state"
    )
    connections: Dict[Tuple[str, str], ConnectionState] = Field(
        default_factory=dict,
        description="Maps (loc1, loc2) to connection state"
    )
    networks: Dict[str, NetworkState] = Field(
        default_factory=dict,
        description="Maps network name to network state"
    )

    @field_serializer('agent_positions')
    def serialize_agent_positions(self, positions: Dict[str, str], _info):
        """Serialize with sorted keys for determinism."""
        return dict(sorted(positions.items()))

    @field_serializer('connections')
    def serialize_connections(self, connections: Dict[Tuple[str, str], ConnectionState], _info):
        """Serialize connection keys as sorted list of tuples."""
        return {
            f"{loc1},{loc2}": conn.model_dump()
            for (loc1, loc2), conn in sorted(connections.items())
        }

    @field_validator('connections', mode='before')
    @classmethod
    def deserialize_connections(cls, v):
        """Deserialize connections from string keys to tuple keys."""
        if isinstance(v, dict):
            result = {}
            for key, value in v.items():
                # If key is already a tuple, use it directly
                if isinstance(key, tuple):
                    result[key] = value if isinstance(value, ConnectionState) else ConnectionState(**value)
                # If key is a string like "loc1,loc2", convert to tuple
                elif isinstance(key, str) and ',' in key:
                    parts = key.split(',', 1)  # Split on first comma only
                    tuple_key = (parts[0], parts[1])
                    result[tuple_key] = value if isinstance(value, ConnectionState) else ConnectionState(**value)
                else:
                    raise ValueError(f"Invalid connection key format: {key}")
            return result
        return v

    @model_validator(mode='after')
    def validate_references(self) -> 'SpatialState':
        """Validate that agent positions and network edges reference valid locations."""
        valid_locations = set(self.locations.keys())

        # Validate agent positions
        for agent_name, location_id in self.agent_positions.items():
            if location_id not in valid_locations:
                raise ValueError(
                    f"Agent '{agent_name}' positioned at invalid location '{location_id}'. "
                    f"Valid locations: {sorted(valid_locations)}"
                )

        # Validate network edges
        for network_name, network_state in self.networks.items():
            for loc1, loc2 in network_state.edges:
                if loc1 not in valid_locations:
                    raise ValueError(
                        f"Network '{network_name}' references invalid location '{loc1}'"
                    )
                if loc2 not in valid_locations:
                    raise ValueError(
                        f"Network '{network_name}' references invalid location '{loc2}'"
                    )

        # Validate connections reference valid locations
        for (loc1, loc2) in self.connections.keys():
            if loc1 not in valid_locations or loc2 not in valid_locations:
                raise ValueError(
                    f"Connection ({loc1}, {loc2}) references invalid location"
                )

        return self


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
    paused_agents: set[str] = Field(default_factory=set)  # Names of paused agents
    auto_resume: Dict[str, int] = Field(default_factory=dict)  # agent_name → turns_remaining
    spatial_state: Optional[SpatialState] = Field(
        default=None,
        description="Optional spatial positioning state"
    )

    @field_serializer('agents')
    def serialize_agents(self, agents: Dict[str, BaseModel], _info):
        """Serialize agents dict properly."""
        return {name: agent.model_dump() for name, agent in agents.items()}

    @field_serializer('global_state')
    def serialize_global_state(self, global_state: BaseModel, _info):
        """Serialize global_state properly."""
        return global_state.model_dump()

    @field_serializer('paused_agents')
    def serialize_paused_agents(self, paused_agents: set[str], _info):
        """Serialize paused_agents set as list for JSON compatibility."""
        return sorted(list(paused_agents))  # Sorted for determinism

    @field_serializer('spatial_state')
    def serialize_spatial_state(self, spatial_state: Optional[SpatialState], _info):
        """Serialize spatial_state if present."""
        if spatial_state is None:
            return None
        return spatial_state.model_dump()


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
