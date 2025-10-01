"""Unit tests for SimulationState JSON serialization."""

import pytest
from llm_sim.models.state import SimulationState, AgentState, GlobalState


def test_simulation_state_roundtrip():
    """Test SimulationState round-trip JSON serialization."""
    state = SimulationState(
        turn=5,
        agents={
            "agent1": AgentState(name="agent1", economic_strength=100.0),
            "agent2": AgentState(name="agent2", economic_strength=200.0),
        },
        global_state=GlobalState(
            interest_rate=0.05,
            total_economic_value=300.0,
            gdp_growth=0.02,
            inflation=0.01,
            unemployment=0.05,
        ),
    )

    # Serialize to JSON
    json_str = state.model_dump_json()

    # Deserialize from JSON
    loaded_state = SimulationState.model_validate_json(json_str)

    # Verify fields
    assert loaded_state.turn == state.turn
    assert len(loaded_state.agents) == 2
    assert loaded_state.agents["agent1"].name == "agent1"
    assert loaded_state.agents["agent1"].economic_strength == 100.0
    assert loaded_state.global_state.interest_rate == 0.05


def test_nested_fields_serialize():
    """Test all nested fields serialize correctly."""
    state = SimulationState(
        turn=1,
        agents={
            "test": AgentState(name="test", economic_strength=50.0),
        },
        global_state=GlobalState(interest_rate=0.03),
    )

    json_str = state.model_dump_json()
    loaded = SimulationState.model_validate_json(json_str)

    assert loaded.global_state.interest_rate == 0.03
    assert loaded.agents["test"].economic_strength == 50.0


def test_no_circular_references():
    """Test no circular references in serialization."""
    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(interest_rate=0.05),
    )

    # Should not raise any errors
    json_str = state.model_dump_json()
    assert json_str is not None
    assert isinstance(json_str, str)
