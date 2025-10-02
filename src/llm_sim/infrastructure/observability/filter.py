"""Variable filtering logic for partial observability.

This module provides filtering of state variables based on observability levels
and variable visibility configurations.
"""

from typing import Any, Dict
from pydantic import BaseModel

from llm_sim.infrastructure.observability.config import (
    ObservabilityLevel,
    VariableVisibilityConfig,
)


def filter_variables(
    state: BaseModel,
    level: ObservabilityLevel,
    visibility_config: VariableVisibilityConfig,
) -> Dict[str, Any]:
    """Filter state variables based on observability level.

    Args:
        state: Agent or global state model
        level: Observability level (UNAWARE/EXTERNAL/INSIDER)
        visibility_config: Which variables are external vs internal

    Returns:
        Dict of {variable_name: value} for visible variables only
    """
    if level == ObservabilityLevel.UNAWARE:
        return {}  # Should not be called, but safe

    state_dict = state.model_dump()

    if level == ObservabilityLevel.INSIDER:
        return state_dict  # All variables visible

    # EXTERNAL: filter to external variables only
    filtered = {}

    # Always include 'name' if present (required field for agent states)
    if "name" in state_dict:
        filtered["name"] = state_dict["name"]

    for var_name in visibility_config.external:
        if var_name in state_dict:
            filtered[var_name] = state_dict[var_name]
    return filtered
