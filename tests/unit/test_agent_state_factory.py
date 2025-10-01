"""Unit tests for dynamic AgentState model creation.

These tests validate the create_agent_state_model() factory function.
These tests should FAIL until the factory is implemented.
"""

import pytest
from pydantic import ValidationError
from llm_sim.models.config import VariableDefinition
from llm_sim.models.state import create_agent_state_model


class TestAgentStateCreation:
    """Tests for creating dynamic AgentState models."""

    def test_create_model_with_float_variable(self):
        """Should create model with float field."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)

        # Create instance
        agent = AgentState(name="Nation_A", gdp=5000.0)
        assert agent.name == "Nation_A"
        assert agent.gdp == 5000.0

    def test_create_model_with_int_variable_and_constraints(self):
        """Should create model with int field and constraints."""
        var_defs = {"population": VariableDefinition(type="int", min=1, max=10000000, default=1000000)}

        AgentState = create_agent_state_model(var_defs)

        # Create instance
        agent = AgentState(name="Nation_A", population=1500000)
        assert agent.population == 1500000

    def test_create_model_with_bool_variable(self):
        """Should create model with bool field."""
        var_defs = {"active": VariableDefinition(type="bool", default=True)}

        AgentState = create_agent_state_model(var_defs)

        # Create instance
        agent = AgentState(name="Nation_A", active=False)
        assert agent.active is False

    def test_create_model_with_categorical_variable(self):
        """Should create model with categorical field."""
        var_defs = {
            "tech_level": VariableDefinition(
                type="categorical", values=["stone", "bronze", "iron"], default="stone"
            )
        }

        AgentState = create_agent_state_model(var_defs)

        # Create instance
        agent = AgentState(name="Nation_A", tech_level="bronze")
        assert agent.tech_level == "bronze"

    def test_model_has_name_field_required(self):
        """Created model should have 'name' as required field."""
        var_defs = {"gdp": VariableDefinition(type="float", default=0.0)}

        AgentState = create_agent_state_model(var_defs)

        # Missing name should raise error
        with pytest.raises(ValidationError):
            AgentState(gdp=1000.0)

    def test_model_is_frozen_immutable(self):
        """Created model should be frozen (immutable)."""
        var_defs = {"gdp": VariableDefinition(type="float", default=0.0)}

        AgentState = create_agent_state_model(var_defs)
        agent = AgentState(name="Nation_A", gdp=1000.0)

        # Attempting to modify should raise error
        with pytest.raises(ValidationError):
            agent.gdp = 2000.0

    def test_constraint_violation_on_creation_raises_error(self):
        """Should raise ValidationError when constraint is violated."""
        var_defs = {"gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)}

        AgentState = create_agent_state_model(var_defs)

        # Value below min should fail
        with pytest.raises(ValidationError):
            AgentState(name="Nation_A", gdp=-100.0)

        # Value above max should fail
        with pytest.raises(ValidationError):
            AgentState(name="Nation_A", gdp=2000000.0)

    def test_categorical_constraint_enforced(self):
        """Should enforce categorical values constraint."""
        var_defs = {
            "tech_level": VariableDefinition(
                type="categorical", values=["stone", "bronze", "iron"], default="stone"
            )
        }

        AgentState = create_agent_state_model(var_defs)

        # Invalid value should fail
        with pytest.raises(ValidationError):
            AgentState(name="Nation_A", tech_level="steel")

    def test_multiple_variables_combined(self):
        """Should handle multiple variables of different types."""
        var_defs = {
            "gdp": VariableDefinition(type="float", min=0, default=1000.0),
            "population": VariableDefinition(type="int", min=1, default=1000000),
            "active": VariableDefinition(type="bool", default=True),
            "tech_level": VariableDefinition(
                type="categorical", values=["low", "medium", "high"], default="low"
            ),
        }

        AgentState = create_agent_state_model(var_defs)

        agent = AgentState(
            name="Nation_A", gdp=5000.0, population=2000000, active=True, tech_level="high"
        )
        assert agent.gdp == 5000.0
        assert agent.population == 2000000
        assert agent.active is True
        assert agent.tech_level == "high"
