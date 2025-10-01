"""Shared test fixtures and utilities."""

import pytest
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    ValidatorConfig,
    LoggingConfig,
    TerminationConditions,
    VariableDefinition,
    get_variable_definitions,
)
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model


@pytest.fixture
def mock_config():
    """Create a minimal valid SimulationConfig for testing."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="Test Simulation",
            max_turns=10,
            termination=TerminationConditions()
        ),
        engine=EngineConfig(
            type="economic",
            interest_rate=0.05
        ),
        agents=[],
        validator=ValidatorConfig(type="always_valid"),
        logging=LoggingConfig()
    )


@pytest.fixture
def legacy_variable_definitions():
    """Provide legacy economic simulation variable definitions."""
    agent_var_defs = {
        "economic_strength": VariableDefinition(type="float", min=0, default=0.0)
    }
    global_var_defs = {
        "interest_rate": VariableDefinition(type="float", default=0.05),
        "total_economic_value": VariableDefinition(type="float", default=0.0),
        "gdp_growth": VariableDefinition(type="float", default=0.0),
        "inflation": VariableDefinition(type="float", default=0.0),
        "unemployment": VariableDefinition(type="float", default=0.0),
    }
    return agent_var_defs, global_var_defs


@pytest.fixture
def AgentState(legacy_variable_definitions):
    """Create legacy-compatible AgentState model."""
    agent_var_defs, _ = legacy_variable_definitions
    return create_agent_state_model(agent_var_defs)


@pytest.fixture
def GlobalState(legacy_variable_definitions):
    """Create legacy-compatible GlobalState model."""
    _, global_var_defs = legacy_variable_definitions
    return create_global_state_model(global_var_defs)


@pytest.fixture
def mock_global_state(GlobalState):
    """Create a minimal valid GlobalState for testing (using dynamic model)."""
    return GlobalState(interest_rate=0.05)


@pytest.fixture
def mock_simulation_state(mock_global_state):
    """Create a minimal valid SimulationState for testing."""
    return SimulationState(
        turn=1,
        agents={},
        global_state=mock_global_state
    )
