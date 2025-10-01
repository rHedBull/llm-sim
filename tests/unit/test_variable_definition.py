"""Unit tests for VariableDefinition validation.

These tests validate the VariableDefinition Pydantic model.
These tests should FAIL until the model is implemented.
"""

import pytest
from pydantic import ValidationError
from llm_sim.models.config import VariableDefinition


class TestFloatVariables:
    """Tests for float type variable definitions."""

    def test_float_with_min_max_validates_correctly(self):
        """Float variable with min/max constraints should validate."""
        var = VariableDefinition(type="float", min=0.0, max=1000.0, default=100.0)
        assert var.type == "float"
        assert var.min == 0.0
        assert var.max == 1000.0
        assert var.default == 100.0

    def test_float_without_constraints(self):
        """Float variable without min/max should validate."""
        var = VariableDefinition(type="float", default=50.0)
        assert var.type == "float"
        assert var.default == 50.0

    def test_float_min_greater_than_max_raises_error(self):
        """Float with min > max should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="float", min=100.0, max=10.0, default=50.0)

    def test_float_default_below_min_raises_error(self):
        """Float with default < min should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="float", min=0.0, max=100.0, default=-10.0)

    def test_float_default_above_max_raises_error(self):
        """Float with default > max should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="float", min=0.0, max=100.0, default=200.0)


class TestIntVariables:
    """Tests for int type variable definitions."""

    def test_int_with_constraints_validates_correctly(self):
        """Int variable with min/max constraints should validate."""
        var = VariableDefinition(type="int", min=1, max=1000000, default=1000)
        assert var.type == "int"
        assert var.min == 1
        assert var.max == 1000000
        assert var.default == 1000

    def test_int_min_greater_than_max_raises_error(self):
        """Int with min > max should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="int", min=100, max=10, default=50)

    def test_int_default_outside_bounds_raises_error(self):
        """Int with default outside [min, max] should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="int", min=0, max=100, default=150)


class TestBoolVariables:
    """Tests for bool type variable definitions."""

    def test_bool_with_default_validates_correctly(self):
        """Boolean variable should validate with bool default."""
        var = VariableDefinition(type="bool", default=True)
        assert var.type == "bool"
        assert var.default is True

    def test_bool_false_default(self):
        """Boolean variable with False default should validate."""
        var = VariableDefinition(type="bool", default=False)
        assert var.default is False


class TestCategoricalVariables:
    """Tests for categorical type variable definitions."""

    def test_categorical_with_values_validates_correctly(self):
        """Categorical variable with values list should validate."""
        var = VariableDefinition(
            type="categorical", values=["bronze", "iron", "steel"], default="bronze"
        )
        assert var.type == "categorical"
        assert var.values == ["bronze", "iron", "steel"]
        assert var.default == "bronze"

    def test_categorical_default_not_in_values_raises_error(self):
        """Categorical with default not in values should raise error."""
        with pytest.raises(ValidationError):
            VariableDefinition(
                type="categorical", values=["bronze", "iron", "steel"], default="gold"
            )

    def test_categorical_without_values_raises_error(self):
        """Categorical without values field should raise error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="categorical", default="value")

    def test_categorical_empty_values_raises_error(self):
        """Categorical with empty values list should raise error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="categorical", values=[], default="value")


class TestInvalidTypes:
    """Tests for invalid variable types."""

    def test_invalid_type_raises_error(self):
        """Unsupported type should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="complex_number", default=0)

    def test_missing_type_raises_error(self):
        """Missing type field should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(default=0)

    def test_missing_default_raises_error(self):
        """Missing default field should raise validation error."""
        with pytest.raises(ValidationError):
            VariableDefinition(type="float", min=0, max=100)
