"""Unit tests for SimulationState JSON serialization."""

import pytest
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model
from llm_sim.models.config import VariableDefinition


def test_simulation_state_roundtrip():
    """Test SimulationState round-trip JSON serialization."""
    # Create dynamic models for legacy economic simulation
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
    AgentState = create_agent_state_model(agent_var_defs)
    GlobalState = create_global_state_model(global_var_defs)

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

    # Test serialization to JSON (verify no errors)
    json_str = state.model_dump_json()
    assert json_str is not None
    assert isinstance(json_str, str)
    assert "agent1" in json_str
    assert "agent2" in json_str

    # Test serialization to dict
    state_dict = state.model_dump(mode='python')
    assert state_dict["turn"] == 5
    assert len(state_dict["agents"]) == 2

    # For dynamic models, we can reconstruct if we have the model classes
    # This mimics what the checkpoint system does (it stores schema_hash to know which models to use)
    loaded_state = SimulationState(
        turn=state_dict["turn"],
        agents={
            name: AgentState.model_validate(agent_data)
            for name, agent_data in state_dict["agents"].items()
        },
        global_state=GlobalState.model_validate(state_dict["global_state"]),
    )

    # Verify fields
    assert loaded_state.turn == state.turn
    assert len(loaded_state.agents) == 2
    assert loaded_state.agents["agent1"].name == "agent1"
    assert loaded_state.agents["agent1"].economic_strength == 100.0
    assert loaded_state.global_state.interest_rate == 0.05


def test_nested_fields_serialize():
    """Test all nested fields serialize correctly."""
    agent_var_defs = {
        "economic_strength": VariableDefinition(type="float", min=0, default=0.0)
    }
    global_var_defs = {
        "interest_rate": VariableDefinition(type="float", default=0.05),
    }
    AgentState = create_agent_state_model(agent_var_defs)
    GlobalState = create_global_state_model(global_var_defs)

    state = SimulationState(
        turn=1,
        agents={
            "test": AgentState(name="test", economic_strength=50.0),
        },
        global_state=GlobalState(interest_rate=0.03),
    )

    json_str = state.model_dump_json()
    assert json_str is not None

    # Serialize to dict and back (works with dynamic models)
    state_dict = state.model_dump(mode='python')
    loaded = SimulationState(
        turn=state_dict["turn"],
        agents={
            name: AgentState.model_validate(agent_data)
            for name, agent_data in state_dict["agents"].items()
        },
        global_state=GlobalState.model_validate(state_dict["global_state"]),
    )

    assert loaded.global_state.interest_rate == 0.03
    assert loaded.agents["test"].economic_strength == 50.0


def test_no_circular_references():
    """Test no circular references in serialization."""
    global_var_defs = {
        "interest_rate": VariableDefinition(type="float", default=0.05),
    }
    GlobalState = create_global_state_model(global_var_defs)

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(interest_rate=0.05),
    )

    # Should not raise any errors
    json_str = state.model_dump_json()
    assert json_str is not None
    assert isinstance(json_str, str)
