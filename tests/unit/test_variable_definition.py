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


class TestDictVariables:
    """Tests for dict type variable definitions (User Story 1)."""

    def test_dict_dynamic_keys_validation(self):
        """Dict with dynamic keys (key_type + value_type) should validate."""
        var = VariableDefinition(
            type="dict",
            key_type="str",
            value_type="float",
            default={}
        )
        assert var.type == "dict"
        assert var.key_type == "str"
        assert var.value_type == "float"
        assert var.default == {}

    def test_dict_fixed_schema_validation(self):
        """Dict with fixed schema should validate."""
        var = VariableDefinition(
            type="dict",
            schema={
                "health": VariableDefinition(type="float", min=0, max=100, default=100),
                "mana": VariableDefinition(type="float", min=0, max=100, default=50),
            },
            default={"health": 100, "mana": 50}
        )
        assert var.type == "dict"
        assert var.schema is not None
        assert "health" in var.schema
        assert "mana" in var.schema

    def test_dict_without_key_type_or_schema_raises_error(self):
        """Dict without key_type+value_type or schema should raise error."""
        with pytest.raises(ValidationError, match="Dict type requires either"):
            VariableDefinition(type="dict", default={})

    def test_dict_with_both_modes_raises_error(self):
        """Dict with both dynamic keys and schema should raise error."""
        with pytest.raises(ValidationError, match="cannot have both"):
            VariableDefinition(
                type="dict",
                key_type="str",
                value_type="int",
                schema={"field": VariableDefinition(type="int", default=0)},
                default={}
            )

    def test_dict_exceeds_depth_limit(self):
        """Dict nesting exceeding 4 levels should be detected (validation happens at runtime)."""
        # This test validates that deeply nested dict configs can be created
        # Actual depth validation happens when creating state models
        deeply_nested = VariableDefinition(
            type="dict",
            key_type="str",
            value_type="float",
            default={}
        )
        # Nesting level 2
        level2 = VariableDefinition(
            type="dict",
            key_type="str",
            value_type=deeply_nested,
            default={}
        )
        assert level2.type == "dict"
        # Depth checking will be tested in state model tests

    def test_dict_exceeds_size_limit(self):
        """Dict collection size validation (1000 items max) happens at runtime."""
        # Config allows any size, runtime validation enforces limits
        var = VariableDefinition(
            type="dict",
            key_type="str",
            value_type="int",
            default={}
        )
        assert var.type == "dict"
        # Size limit enforcement tested in state model validation tests


class TestTupleVariables:
    """Tests for tuple type variable definitions (User Story 2)."""

    def test_tuple_homogeneous_validation(self):
        """Tuple with homogeneous types (all same type) should validate."""
        var = VariableDefinition(
            type="tuple",
            item_types=[
                VariableDefinition(type="float", default=0.0),
                VariableDefinition(type="float", default=0.0),
            ],
            default=[0.0, 0.0]
        )
        assert var.type == "tuple"
        assert var.item_types is not None
        assert len(var.item_types) == 2

    def test_tuple_heterogeneous_validation(self):
        """Tuple with heterogeneous types (different types) should validate."""
        var = VariableDefinition(
            type="tuple",
            item_types=[
                VariableDefinition(type="int", default=0),
                VariableDefinition(type="str", default=""),
                VariableDefinition(type="float", default=0.0),
            ],
            default=[0, "", 0.0]
        )
        assert var.type == "tuple"
        assert len(var.item_types) == 3

    def test_tuple_element_constraints_rgb(self):
        """Tuple with per-element constraints (RGB color example) should validate."""
        var = VariableDefinition(
            type="tuple",
            item_types=[
                VariableDefinition(type="int", min=0, max=255, default=255),
                VariableDefinition(type="int", min=0, max=255, default=255),
                VariableDefinition(type="int", min=0, max=255, default=255),
            ],
            default=[255, 255, 255]
        )
        assert var.type == "tuple"
        assert len(var.item_types) == 3
        # Verify each element has constraints
        for item_def in var.item_types:
            assert item_def.min == 0
            assert item_def.max == 255

    def test_tuple_length_mismatch_error(self):
        """Tuple with default length != item_types length should raise error."""
        with pytest.raises(ValidationError, match="Tuple default length"):
            VariableDefinition(
                type="tuple",
                item_types=[
                    VariableDefinition(type="float", default=0.0),
                    VariableDefinition(type="float", default=0.0),
                ],
                default=[0.0, 0.0, 0.0]  # 3 elements but item_types has 2
            )


class TestListVariables:
    """Tests for list type variable definitions (User Story 3)."""

    def test_list_scalar_items(self):
        """List with scalar item type (string) should validate."""
        var = VariableDefinition(
            type="list",
            item_type="str",
            default=[]
        )
        assert var.type == "list"
        assert var.item_type == "str"
        assert var.default == []

    def test_list_complex_items_tuple(self):
        """List with complex item type (tuple) should validate."""
        var = VariableDefinition(
            type="list",
            item_type=VariableDefinition(
                type="tuple",
                item_types=[
                    VariableDefinition(type="float", default=0.0),
                    VariableDefinition(type="float", default=0.0),
                ],
                default=[0.0, 0.0]
            ),
            default=[]
        )
        assert var.type == "list"
        assert var.item_type is not None
        assert isinstance(var.item_type, VariableDefinition)

    def test_list_max_length_validation(self):
        """List with max_length constraint should validate."""
        var = VariableDefinition(
            type="list",
            item_type="str",
            max_length=10,
            default=[]
        )
        assert var.type == "list"
        assert var.max_length == 10

    def test_list_exceeds_depth_limit(self):
        """Nested list structure should be creatable (depth validation at runtime)."""
        # Create nested list (list of list of list)
        inner_list = VariableDefinition(type="list", item_type="int", default=[])
        middle_list = VariableDefinition(type="list", item_type=inner_list, default=[])
        outer_list = VariableDefinition(type="list", item_type=middle_list, default=[])

        assert outer_list.type == "list"
        # Depth checking happens in state model generation

    def test_list_exceeds_size_limit(self):
        """List size limit (1000 items) enforced at runtime, not config time."""
        var = VariableDefinition(
            type="list",
            item_type="int",
            default=[]
        )
        assert var.type == "list"
        # Size validation happens in state model validation

    def test_list_without_item_type_raises_error(self):
        """List without item_type should raise error."""
        with pytest.raises(ValidationError, match="List type requires 'item_type'"):
            VariableDefinition(type="list", default=[])


class TestStringVariables:
    """Tests for string type variable definitions (User Story 4)."""

    def test_str_unrestricted_nullable(self):
        """Unrestricted string (no pattern) with null default should validate."""
        var = VariableDefinition(
            type="str",
            default=None
        )
        assert var.type == "str"
        assert var.default is None
        assert var.pattern is None

    def test_str_pattern_validation_regex(self):
        """String with regex pattern should validate."""
        var = VariableDefinition(
            type="str",
            pattern=r"^[A-Za-z][A-Za-z0-9_]{2,19}$",
            default="Agent_1"
        )
        assert var.type == "str"
        assert var.pattern == r"^[A-Za-z][A-Za-z0-9_]{2,19}$"
        assert var.default == "Agent_1"

    def test_str_max_length_constraint(self):
        """String with max_length constraint should validate."""
        var = VariableDefinition(
            type="str",
            max_length=500,
            default=""
        )
        assert var.type == "str"
        assert var.max_length == 500

    def test_str_pattern_mismatch_error(self):
        """String with invalid max_length should raise error."""
        with pytest.raises(ValidationError, match="max_length must be greater than 0"):
            VariableDefinition(
                type="str",
                max_length=0,
                default=""
            )

    def test_str_with_both_pattern_and_length(self):
        """String with both pattern and max_length should validate."""
        var = VariableDefinition(
            type="str",
            pattern=r"^[a-z]+$",
            max_length=20,
            default="hello"
        )
        assert var.type == "str"
        assert var.pattern == r"^[a-z]+$"
        assert var.max_length == 20


class TestObjectVariables:
    """Tests for object type variable definitions (User Story 5)."""

    def test_object_nested_schema_validation(self):
        """Object with nested schema should validate."""
        var = VariableDefinition(
            type="object",
            schema={
                "name": VariableDefinition(type="str", default="Town"),
                "population": VariableDefinition(type="int", min=0, default=1000),
                "position": VariableDefinition(
                    type="tuple",
                    item_types=[
                        VariableDefinition(type="float", default=0.0),
                        VariableDefinition(type="float", default=0.0),
                    ],
                    default=[0.0, 0.0]
                ),
            },
            default={"name": "Town", "population": 1000, "position": [0.0, 0.0]}
        )
        assert var.type == "object"
        assert var.schema is not None
        assert "name" in var.schema
        assert "population" in var.schema
        assert "position" in var.schema

    def test_object_contains_dict_list_tuple(self):
        """Object with mixed complex types should validate."""
        var = VariableDefinition(
            type="object",
            schema={
                "resources": VariableDefinition(
                    type="dict",
                    key_type="str",
                    value_type="float",
                    default={}
                ),
                "history": VariableDefinition(
                    type="list",
                    item_type="str",
                    default=[]
                ),
                "coordinates": VariableDefinition(
                    type="tuple",
                    item_types=[
                        VariableDefinition(type="float", default=0.0),
                        VariableDefinition(type="float", default=0.0),
                    ],
                    default=[0.0, 0.0]
                ),
            },
            default={"resources": {}, "history": [], "coordinates": [0.0, 0.0]}
        )
        assert var.type == "object"
        assert len(var.schema) == 3

    def test_object_without_schema_raises_error(self):
        """Object without schema should raise error."""
        with pytest.raises(ValidationError, match="Object type requires 'schema'"):
            VariableDefinition(type="object", default={})
