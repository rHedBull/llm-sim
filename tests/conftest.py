"""Shared test fixtures and utilities."""

import pytest
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    ValidatorConfig,
    LoggingConfig,
    TerminationConditions,
)
from llm_sim.models.state import GlobalState, SimulationState


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
def mock_global_state():
    """Create a minimal valid GlobalState for testing."""
    return GlobalState(interest_rate=0.05)


@pytest.fixture
def mock_simulation_state(mock_global_state):
    """Create a minimal valid SimulationState for testing."""
    return SimulationState(
        turn=1,
        agents={},
        global_state=mock_global_state
    )
