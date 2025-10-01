"""Unit tests for state updates with validation.

These tests validate that state updates via model_copy() enforce constraints.
These tests should FAIL until dynamic state models are implemented.
"""

import pytest
from pydantic import ValidationError
from llm_sim.models.config import VariableDefinition
from llm_sim.models.state import create_agent_state_model, create_global_state_model


class TestAgentStateUpdates:
    """Tests for agent state updates with validation."""

    def test_valid_update_via_model_copy_succeeds(self):
        """Valid update via model_copy() should succeed."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", gdp=1000.0)

        # Update should succeed
        new_agent = agent.model_copy(update={"gdp": 5000.0})
        assert new_agent.gdp == 5000.0
        assert agent.gdp == 1000.0  # Original unchanged

    def test_update_violating_min_constraint_rejected(self):
        """Update violating min constraint should be rejected."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", gdp=1000.0)

        # Update below min should fail
        with pytest.raises(ValidationError):
            agent.model_copy(update={"gdp": -100.0})

    def test_update_violating_max_constraint_rejected(self):
        """Update violating max constraint should be rejected."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", gdp=1000.0)

        # Update above max should fail
        with pytest.raises(ValidationError):
            agent.model_copy(update={"gdp": 2000000.0})

    def test_invalid_categorical_value_rejected(self):
        """Update with invalid categorical value should be rejected."""
        var_defs = {
            "tech_level": VariableDefinition(
                type="categorical", values=["stone", "bronze", "iron"], default="stone"
            )
        }

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", tech_level="stone")

        # Invalid value should fail
        with pytest.raises(ValidationError):
            agent.model_copy(update={"tech_level": "steel"})

    def test_type_mismatch_rejected(self):
        """Update with wrong type should be rejected."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", gdp=1000.0)

        # String value for float field should fail
        with pytest.raises(ValidationError):
            agent.model_copy(update={"gdp": "not a number"})


class TestGlobalStateUpdates:
    """Tests for global state updates with validation."""

    def test_valid_update_succeeds(self):
        """Valid global state update should succeed."""
        var_defs = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.0)
        }

        GlobalState = create_global_state_model(var_defs)
        state = GlobalState(inflation=0.02)

        # Update should succeed
        new_state = state.model_copy(update={"inflation": 0.05})
        assert new_state.inflation == 0.05
        assert state.inflation == 0.02  # Original unchanged

    def test_constraint_violation_rejected(self):
        """Update violating constraints should be rejected."""
        var_defs = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.0)
        }

        GlobalState = create_global_state_model(var_defs)
        state = GlobalState(inflation=0.02)

        # Update outside bounds should fail
        with pytest.raises(ValidationError):
            state.model_copy(update={"inflation": 2.0})

    def test_multiple_field_update(self):
        """Should handle multiple field updates at once."""
        var_defs = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.0),
            "world_peace": VariableDefinition(type="bool", default=True),
        }

        GlobalState = create_global_state_model(var_defs)
        state = GlobalState(inflation=0.02, world_peace=True)

        # Multiple updates should work
        new_state = state.model_copy(update={"inflation": 0.03, "world_peace": False})
        assert new_state.inflation == 0.03
        assert new_state.world_peace is False
