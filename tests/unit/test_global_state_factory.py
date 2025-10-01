"""Unit tests for dynamic GlobalState model creation.

These tests validate the create_global_state_model() factory function.
These tests should FAIL until the factory is implemented.
"""

import pytest
from pydantic import ValidationError
from llm_sim.models.config import VariableDefinition
from llm_sim.models.state import create_global_state_model


class TestGlobalStateCreation:
    """Tests for creating dynamic GlobalState models."""

    def test_create_model_with_mixed_variable_types(self):
        """Should create model with mixed variable types."""
        var_defs = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.02),
            "total_casualties": VariableDefinition(type="int", min=0, default=0),
            "world_peace": VariableDefinition(type="bool", default=True),
            "dominant_tech": VariableDefinition(
                type="categorical", values=["stone", "bronze", "iron"], default="stone"
            ),
        }

        GlobalState = create_global_state_model(var_defs)

        # Create instance
        state = GlobalState(
            inflation=0.03, total_casualties=100, world_peace=False, dominant_tech="iron"
        )
        assert state.inflation == 0.03
        assert state.total_casualties == 100
        assert state.world_peace is False
        assert state.dominant_tech == "iron"

    def test_model_is_frozen_immutable(self):
        """Created model should be frozen (immutable)."""
        var_defs = {"inflation": VariableDefinition(type="float", default=0.0)}

        GlobalState = create_global_state_model(var_defs)
        state = GlobalState(inflation=0.02)

        # Attempting to modify should raise error
        with pytest.raises(ValidationError):
            state.inflation = 0.05

    def test_all_fields_have_correct_types(self):
        """All fields should have correct types from definitions."""
        var_defs = {
            "float_var": VariableDefinition(type="float", default=0.0),
            "int_var": VariableDefinition(type="int", default=0),
            "bool_var": VariableDefinition(type="bool", default=True),
            "cat_var": VariableDefinition(
                type="categorical", values=["a", "b", "c"], default="a"
            ),
        }

        GlobalState = create_global_state_model(var_defs)

        state = GlobalState(float_var=1.5, int_var=10, bool_var=False, cat_var="b")

        assert isinstance(state.float_var, float)
        assert isinstance(state.int_var, int)
        assert isinstance(state.bool_var, bool)
        assert isinstance(state.cat_var, str)

    def test_constraint_enforcement_works(self):
        """Should enforce constraints on field values."""
        var_defs = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.0)
        }

        GlobalState = create_global_state_model(var_defs)

        # Value outside bounds should fail
        with pytest.raises(ValidationError):
            GlobalState(inflation=2.0)

        with pytest.raises(ValidationError):
            GlobalState(inflation=-2.0)

    def test_empty_variable_definitions(self):
        """Should handle empty variable definitions."""
        var_defs = {}

        GlobalState = create_global_state_model(var_defs)

        # Should create model with no custom fields
        state = GlobalState()
        assert state is not None
