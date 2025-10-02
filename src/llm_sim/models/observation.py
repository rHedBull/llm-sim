"""Observation construction logic for partial observability.

This module provides the core construct_observation function that integrates
all observability components to create filtered, noisy observations for agents.
"""

from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, create_model

from llm_sim.models.state import SimulationState
from llm_sim.infrastructure.observability.config import (
    ObservabilityConfig,
    ObservabilityLevel,
)
from llm_sim.infrastructure.observability.matrix import ObservabilityMatrix
from llm_sim.infrastructure.observability.filter import filter_variables
from llm_sim.infrastructure.observability.noise import apply_noise
from llm_sim.utils.logging import get_logger

logger = get_logger(__name__)


def _create_filtered_model(field_dict: Dict[str, Any], model_name: str) -> BaseModel:
    """Create a Pydantic model dynamically from a field dictionary.

    Args:
        field_dict: Dictionary of {field_name: field_value}
        model_name: Name for the dynamically created model

    Returns:
        Instance of dynamically created Pydantic model
    """
    # Build fields specification for create_model
    # Format: {field_name: (field_type, field_value)}
    fields = {}
    for field_name, field_value in field_dict.items():
        field_type = type(field_value)
        fields[field_name] = (field_type, field_value)

    # Create the model class
    model_class = create_model(
        model_name,
        __config__=ConfigDict(frozen=True, arbitrary_types_allowed=True),
        **fields,
    )

    # Create an instance with the provided values
    return model_class(**field_dict)


def _apply_noise_to_variables(
    variables: Dict[str, Any],
    noise_factor: float,
    turn: int,
    observer_id: str,
    target_prefix: str,
) -> tuple[Dict[str, Any], list]:
    """Apply noise to numeric variables and track changes.

    Args:
        variables: Dictionary of variable names to values
        noise_factor: Noise factor to apply (0.0 = no noise)
        turn: Current simulation turn (for seeding)
        observer_id: ID of observer (for seeding)
        target_prefix: Prefix for seed (e.g., "Agent1" or "global")

    Returns:
        Tuple of (noisy_variables_dict, noise_log_list)
    """
    noisy_vars = {}
    noisy_log = []

    for var_name, var_value in variables.items():
        if isinstance(var_value, (int, float)) and var_name != "name":
            noisy_value = apply_noise(
                float(var_value),
                noise_factor,
                (turn, observer_id, f"{target_prefix}.{var_name}"),
            )
            noisy_vars[var_name] = type(var_value)(noisy_value)  # Preserve type
            if noise_factor > 0.0:
                noisy_log.append({
                    "variable": var_name,
                    "original": var_value,
                    "noisy": noisy_vars[var_name],
                    "noise_factor": noise_factor,
                })
        else:
            noisy_vars[var_name] = var_value

    return noisy_vars, noisy_log


def construct_observation(
    observer_id: str, ground_truth: SimulationState, config: ObservabilityConfig | None
) -> SimulationState:
    """Construct filtered observation for an agent based on observability config.

    Args:
        observer_id: ID of the observing agent
        ground_truth: Complete simulation state (ground truth)
        config: Observability configuration (None = full visibility)

    Returns:
        New SimulationState with filtered agents, filtered/noisy variables
    """
    # Backward compatibility: if config is None or disabled, return full ground truth
    if config is None or not config.enabled:
        logger.info(
            "observation_construction_bypassed",
            observer=observer_id,
            turn=ground_truth.turn,
            reason="observability_disabled" if config and not config.enabled else "no_config",
        )
        # Return ground truth with empty reasoning chains
        return SimulationState(
            turn=ground_truth.turn,
            agents=ground_truth.agents,
            global_state=ground_truth.global_state,
            reasoning_chains=[],
        )

    # Initialize observability matrix
    matrix = ObservabilityMatrix(config.matrix, config.default)

    # Filter agents
    filtered_agents = {}
    excluded_agents = []
    included_agents = []

    for agent_id, agent_state in ground_truth.agents.items():
        level, noise = matrix.get_observability(observer_id, agent_id)

        if level == ObservabilityLevel.UNAWARE:
            excluded_agents.append(agent_id)
            continue  # Skip this agent

        included_agents.append(agent_id)

        # Filter variables based on level
        visible_vars = filter_variables(agent_state, level, config.variable_visibility)

        # Apply noise to numeric variables
        noisy_vars, noisy_variables = _apply_noise_to_variables(
            visible_vars, noise, ground_truth.turn, observer_id, agent_id
        )

        # Log noise application for this agent
        if noisy_variables:
            logger.info(
                "noise_applied",
                observer=observer_id,
                target=agent_id,
                turn=ground_truth.turn,
                variables=noisy_variables,
            )

        # Create new agent state instance with only filtered/noisy values
        # This creates a new model class with only the visible fields
        filtered_agents[agent_id] = _create_filtered_model(
            noisy_vars, f"FilteredAgentState_{agent_id}"
        )

    # Log agent filtering summary
    logger.info(
        "observation_filtered.agents_filtered",
        observer=observer_id,
        turn=ground_truth.turn,
        total_agents=len(ground_truth.agents),
        included_agents=included_agents,
        excluded_agents=excluded_agents,
    )

    # Filter and noise global state
    global_level, global_noise = matrix.get_observability(observer_id, "global")

    if global_level == ObservabilityLevel.UNAWARE:
        # Create empty global state
        global_visible_vars = {}
        logger.info(
            "observation_filtered.global_state_filtered",
            observer=observer_id,
            turn=ground_truth.turn,
            level="unaware",
            visible_variables=[],
        )
    else:
        global_visible_vars = filter_variables(
            ground_truth.global_state, global_level, config.variable_visibility
        )
        logger.info(
            "observation_filtered.global_state_filtered",
            observer=observer_id,
            turn=ground_truth.turn,
            level=global_level.value,
            visible_variables=list(global_visible_vars.keys()),
        )

    # Apply noise to global variables
    noisy_global_vars, noisy_global_variables = _apply_noise_to_variables(
        global_visible_vars, global_noise, ground_truth.turn, observer_id, "global"
    )

    # Log noise application for global state
    if noisy_global_variables:
        logger.info(
            "noise_applied",
            observer=observer_id,
            target="global",
            turn=ground_truth.turn,
            variables=noisy_global_variables,
        )

    # Create filtered global state model
    filtered_global_state = _create_filtered_model(
        noisy_global_vars, "FilteredGlobalState"
    )

    # Return new SimulationState with filtered data
    return SimulationState(
        turn=ground_truth.turn,
        agents=filtered_agents,
        global_state=filtered_global_state,
        reasoning_chains=[],  # Observations don't include others' reasoning
    )
