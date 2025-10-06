"""Configuration models for the simulation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import structlog
import yaml

logger = structlog.get_logger(__name__)


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


class GridConfig(BaseModel):
    """Configuration for 2D grid topology."""
    type: Literal["grid"] = "grid"
    width: int = Field(..., gt=0, description="Grid width")
    height: int = Field(..., gt=0, description="Grid height")
    connectivity: Literal[4, 8] = Field(default=4, description="Neighbor connectivity")
    wrapping: bool = Field(default=False, description="Whether grid wraps (toroidal)")


class HexGridConfig(BaseModel):
    """Configuration for hexagonal grid topology."""
    type: Literal["hex_grid"] = "hex_grid"
    radius: int = Field(..., ge=0, description="Hex grid radius")
    coord_system: Literal["axial"] = Field(default="axial", description="Coordinate system")


class NetworkConfig(BaseModel):
    """Configuration for network/graph topology."""
    type: Literal["network"] = "network"
    edges_file: str = Field(..., description="Path to JSON edge list file")

    @field_validator('edges_file')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"Edges file not found: {v}")
        return v


class GeoJSONConfig(BaseModel):
    """Configuration for GeoJSON topology."""
    type: Literal["geojson"] = "geojson"
    geojson_file: str = Field(..., description="Path to GeoJSON file")

    @field_validator('geojson_file')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"GeoJSON file not found: {v}")
        return v


SpatialConfigTypes = Union[GridConfig, HexGridConfig, NetworkConfig, GeoJSONConfig]


class SpatialConfig(BaseModel):
    """Top-level spatial configuration."""
    topology: SpatialConfigTypes = Field(..., discriminator='type')
    location_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Initial attributes per location"
    )
    additional_networks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Additional network layers beyond base topology"
    )


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    type: str
    initial_economic_strength: Optional[float] = None  # Optional for dynamic variable systems
    initial_location: Optional[str] = Field(
        default=None,
        description="Initial location ID for spatial simulations"
    )


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


class VariableDefinition(BaseModel):
    """Definition of a single state variable."""

    type: Literal["float", "int", "bool", "categorical"]
    min: Optional[float] = None
    max: Optional[float] = None
    values: Optional[List[str]] = None
    default: Union[float, int, bool, str]

    @model_validator(mode="after")
    def validate_variable_definition(self) -> "VariableDefinition":
        """Validate variable definition based on type."""
        # Categorical must have values
        if self.type == "categorical":
            if not self.values:
                raise ValueError("Categorical type requires 'values' field")
            if len(self.values) == 0:
                raise ValueError("Categorical 'values' list cannot be empty")
            if self.default not in self.values:
                raise ValueError(
                    f"Default value '{self.default}' must be in values list {self.values}"
                )

        # Numeric types: check min/max constraints
        if self.type in ("float", "int"):
            if self.min is not None and self.max is not None and self.min > self.max:
                raise ValueError(f"min ({self.min}) cannot be greater than max ({self.max})")

            if self.min is not None and self.default < self.min:
                raise ValueError(
                    f"Default value {self.default} is below minimum {self.min}"
                )

            if self.max is not None and self.default > self.max:
                raise ValueError(
                    f"Default value {self.default} is above maximum {self.max}"
                )

        return self


class StateVariablesConfig(BaseModel):
    """Container for agent and global state variable definitions."""

    agent_vars: Dict[str, VariableDefinition]
    global_vars: Dict[str, VariableDefinition]

    @model_validator(mode="after")
    def validate_variable_names(self) -> "StateVariablesConfig":
        """Validate variable names are valid Python identifiers and not reserved."""
        reserved_names = {"name", "turn", "agents", "global_state", "reasoning_chains"}

        for var_name in self.agent_vars.keys():
            if not var_name.isidentifier():
                raise ValueError(f"Variable name '{var_name}' is not a valid Python identifier")
            if var_name in reserved_names:
                raise ValueError(f"Variable name '{var_name}' is reserved and cannot be used")

        for var_name in self.global_vars.keys():
            if not var_name.isidentifier():
                raise ValueError(f"Variable name '{var_name}' is not a valid Python identifier")
            if var_name in reserved_names:
                raise ValueError(f"Variable name '{var_name}' is reserved and cannot be used")

        return self


class SimulationConfig(BaseModel):
    """Complete simulation configuration."""

    simulation: SimulationSettings
    engine: EngineConfig
    agents: List[AgentConfig]
    validator: ValidatorConfig
    logging: Optional[LoggingConfig] = None  # Optional for backward compatibility
    llm: Optional[LLMConfig] = None  # Optional for backward compatibility
    state_variables: Optional[StateVariablesConfig] = None  # Optional for backward compatibility
    observability: Optional[Any] = None  # Optional for backward compatibility - parsed in validator
    spatial: Optional[SpatialConfig] = Field(
        default=None,
        description="Optional spatial topology configuration"
    )

    @field_validator("observability", mode="before")
    @classmethod
    def parse_observability(cls, v: Any) -> Any:
        """Parse observability config with deferred import to avoid circular dependency."""
        if v is None:
            return None

        # Import here to avoid circular dependency
        from llm_sim.infrastructure.observability.config import ObservabilityConfig

        if isinstance(v, ObservabilityConfig):
            return v
        return ObservabilityConfig(**v)

    @model_validator(mode="after")
    def validate_unique_agent_names(self) -> "SimulationConfig":
        """Validate that all agent names are unique."""
        agent_names = [agent.name for agent in self.agents]
        if len(agent_names) != len(set(agent_names)):
            raise ValueError("All agent names must be unique, found duplicates")
        return self

    @model_validator(mode="after")
    def validate_observability_references(self) -> "SimulationConfig":
        """Cross-validate observability config against agent and variable names."""
        if self.observability is None:
            return self

        # Get agent names
        agent_names = {agent.name for agent in self.agents}
        agent_list = sorted(agent_names)

        # Validate observers and targets in matrix
        for entry in self.observability.matrix:
            if entry.observer not in agent_names:
                raise ValueError(
                    f"Unknown observer '{entry.observer}' in observability matrix. "
                    f"Available agents: {agent_list}. "
                    f"Remediation: Verify the observer name matches an agent defined in the 'agents' list."
                )
            if entry.target != "global" and entry.target not in agent_names:
                valid_targets = agent_list + ["global"]
                raise ValueError(
                    f"Unknown target '{entry.target}' in observability matrix. "
                    f"Available targets: {valid_targets}. "
                    f"Remediation: Verify the target name matches an agent defined in the 'agents' list, "
                    f"or use 'global' for global state."
                )

        # Validate variable names if state_variables is configured
        if self.state_variables is not None:
            agent_var_names = set(self.state_variables.agent_vars.keys())
            global_var_names = set(self.state_variables.global_vars.keys())
            all_var_names = agent_var_names | global_var_names
            all_var_list = sorted(all_var_names)

            for var_name in self.observability.variable_visibility.external:
                if var_name not in all_var_names:
                    agent_vars = sorted(agent_var_names)
                    global_vars = sorted(global_var_names)
                    raise ValueError(
                        f"Unknown variable '{var_name}' in external visibility list. "
                        f"Available variables: {all_var_list} "
                        f"(agent variables: {agent_vars}, global variables: {global_vars}). "
                        f"Remediation: Verify the variable name matches a variable defined in "
                        f"'state_variables.agent_vars' or 'state_variables.global_vars'."
                    )

            for var_name in self.observability.variable_visibility.internal:
                if var_name not in all_var_names:
                    agent_vars = sorted(agent_var_names)
                    global_vars = sorted(global_var_names)
                    raise ValueError(
                        f"Unknown variable '{var_name}' in internal visibility list. "
                        f"Available variables: {all_var_list} "
                        f"(agent variables: {agent_vars}, global variables: {global_vars}). "
                        f"Remediation: Verify the variable name matches a variable defined in "
                        f"'state_variables.agent_vars' or 'state_variables.global_vars'."
                    )

        return self


def get_variable_definitions(
    config: SimulationConfig,
) -> tuple[Dict[str, VariableDefinition], Dict[str, VariableDefinition]]:
    """Get variable definitions from config, using defaults if not specified."""
    if config.state_variables is None:
        logger.warning(
            "Config missing 'state_variables' section. "
            "Using legacy default variables. "
            "Please update config to explicit variable definitions."
        )

        # Default agent variables
        default_agent_vars = {
            "economic_strength": VariableDefinition(type="float", min=0, default=0.0)
        }

        # Default global variables
        default_global_vars = {
            "interest_rate": VariableDefinition(type="float", default=0.05),
            "total_economic_value": VariableDefinition(type="float", default=0.0),
            "gdp_growth": VariableDefinition(type="float", default=0.0),
            "inflation": VariableDefinition(type="float", default=0.0),
            "unemployment": VariableDefinition(type="float", default=0.0),
        }

        return default_agent_vars, default_global_vars

    return config.state_variables.agent_vars, config.state_variables.global_vars


def load_config(config_path: Union[str, Path]) -> SimulationConfig:
    """Load simulation configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Parsed and validated SimulationConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValidationError: If config doesn't match schema
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return SimulationConfig(**config_data)
