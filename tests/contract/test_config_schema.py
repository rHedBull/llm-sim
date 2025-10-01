"""Contract tests for config schema validation.

These tests validate the YAML configuration schema for state variables.
They test the JSON schema from specs/007-we-want-to/contracts/config-schema.json
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


@pytest.fixture
def schema():
    """Load the config JSON schema."""
    schema_path = Path("specs/007-we-want-to/contracts/config-schema.json")
    with open(schema_path) as f:
        return json.load(f)


class TestValidConfigs:
    """Tests for valid configuration schemas that should pass validation."""

    def test_valid_config_with_state_variables_passes(self, schema):
        """Valid config with state_variables section should validate."""
        config = {
            "state_variables": {
                "agent_vars": {
                    "gdp": {"type": "float", "min": 0, "max": 1000000, "default": 1000.0}
                },
                "global_vars": {
                    "inflation": {"type": "float", "min": -1.0, "max": 1.0, "default": 0.02}
                },
            }
        }
        validate(instance=config, schema=schema)

    def test_float_variable_with_constraints(self, schema):
        """Float variable with min/max constraints should validate."""
        config = {
            "state_variables": {
                "agent_vars": {
                    "gdp": {"type": "float", "min": 0, "max": 1000000, "default": 1000.0}
                },
                "global_vars": {},
            }
        }
        validate(instance=config, schema=schema)

    def test_int_variable_with_constraints(self, schema):
        """Int variable with min/max constraints should validate."""
        config = {
            "state_variables": {
                "agent_vars": {
                    "population": {"type": "int", "min": 1, "max": 10000000, "default": 1000000}
                },
                "global_vars": {},
            }
        }
        validate(instance=config, schema=schema)

    def test_bool_variable(self, schema):
        """Boolean variable should validate."""
        config = {
            "state_variables": {
                "agent_vars": {},
                "global_vars": {"open_economy": {"type": "bool", "default": True}},
            }
        }
        validate(instance=config, schema=schema)

    def test_categorical_variable(self, schema):
        """Categorical variable with values list should validate."""
        config = {
            "state_variables": {
                "agent_vars": {
                    "tech_level": {
                        "type": "categorical",
                        "values": ["bronze", "iron", "steel"],
                        "default": "bronze",
                    }
                },
                "global_vars": {},
            }
        }
        validate(instance=config, schema=schema)


class TestInvalidConfigs:
    """Tests for invalid configurations that should fail validation."""

    def test_invalid_type_rejected(self, schema):
        """Unsupported variable type should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"score": {"type": "complex_number", "default": 0}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_categorical_without_values_rejected(self, schema):
        """Categorical type without 'values' field should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"level": {"type": "categorical", "default": "high"}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_empty_categorical_values_rejected(self, schema):
        """Categorical with empty values list should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"level": {"type": "categorical", "values": [], "default": "high"}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_missing_default_rejected(self, schema):
        """Variable without 'default' field should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"gdp": {"type": "float", "min": 0}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_float_with_bool_default_rejected(self, schema):
        """Float variable with boolean default should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"gdp": {"type": "float", "min": 0, "default": True}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_bool_with_numeric_default_rejected(self, schema):
        """Boolean variable with numeric default should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {"active": {"type": "bool", "default": 1}},
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_categorical_with_numeric_default_rejected(self, schema):
        """Categorical variable with numeric default should be rejected."""
        config = {
            "state_variables": {
                "agent_vars": {
                    "level": {"type": "categorical", "values": ["low", "high"], "default": 1}
                },
                "global_vars": {},
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
