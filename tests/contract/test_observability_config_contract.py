"""Contract tests for observability configuration schema validation.

These tests validate the observability configuration schema.
They test the JSON schema from specs/008-partial-observability-agents/contracts/observability-config-schema.json

NOTE: This is a TDD test suite. Tests will FAIL until ObservabilityConfig is implemented.
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


@pytest.fixture
def schema():
    """Load the observability config JSON schema."""
    schema_path = Path("specs/008-partial-observability-agents/contracts/observability-config-schema.json")
    with open(schema_path) as f:
        return json.load(f)


class TestValidObservabilityConfigs:
    """Tests for valid observability configurations that should pass validation."""

    def test_valid_config_passes(self, schema):
        """Valid observability config with all required fields should validate."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["economic_strength", "position"],
                "internal": ["secret_reserves", "hidden_strategy"]
            },
            "matrix": [
                ["Agent1", "Agent1", "insider", 0.0],
                ["Agent1", "Agent2", "external", 0.2],
                ["Agent1", "global", "external", 0.1],
                ["Agent2", "Agent1", "unaware", None],
                ["Agent2", "global", "insider", 0.0]
            ],
            "default": {
                "level": "external",
                "noise": 0.15
            }
        }
        validate(instance=config, schema=schema)

    def test_disabled_config_passes(self, schema):
        """Config with enabled=false (full observability) should validate."""
        config = {
            "enabled": False,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": []
        }
        validate(instance=config, schema=schema)

    def test_empty_variable_lists_passes(self, schema):
        """Config with empty external/internal variable lists should validate."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": []
        }
        validate(instance=config, schema=schema)

    def test_all_observability_levels_pass(self, schema):
        """All valid observability levels should validate."""
        for level in ["unaware", "external", "insider"]:
            config = {
                "enabled": True,
                "variable_visibility": {
                    "external": ["var1"],
                    "internal": ["var2"]
                },
                "matrix": [
                    ["Agent1", "Agent2", level, 0.1 if level != "unaware" else None]
                ]
            }
            validate(instance=config, schema=schema)

    def test_zero_noise_passes(self, schema):
        """Observability level with zero noise should validate."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["var1"],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "external", 0.0]
            ]
        }
        validate(instance=config, schema=schema)

    def test_null_noise_for_unaware_passes(self, schema):
        """Unaware level with null noise should validate."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "unaware", None]
            ]
        }
        validate(instance=config, schema=schema)

    def test_config_without_default_passes(self, schema):
        """Config without optional 'default' field should validate."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["var1"],
                "internal": ["var2"]
            },
            "matrix": [
                ["Agent1", "Agent2", "external", 0.1]
            ]
        }
        validate(instance=config, schema=schema)


class TestInvalidObservabilityConfigs:
    """Tests for invalid configurations that should fail validation."""

    def test_missing_enabled_rejected(self, schema):
        """Config missing 'enabled' field should be rejected."""
        config = {
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": []
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_missing_variable_visibility_rejected(self, schema):
        """Config missing 'variable_visibility' field should be rejected."""
        config = {
            "enabled": True,
            "matrix": []
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_missing_matrix_rejected(self, schema):
        """Config missing 'matrix' field should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_observability_level_rejected(self, schema):
        """Invalid observability level should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["var1"],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "invalid_level", 0.1]
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_negative_noise_rejected(self, schema):
        """Negative noise value should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["var1"],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "external", -0.1]
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_missing_external_field_rejected(self, schema):
        """variable_visibility missing 'external' field should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "internal": []
            },
            "matrix": []
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_missing_internal_field_rejected(self, schema):
        """variable_visibility missing 'internal' field should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": []
            },
            "matrix": []
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_matrix_entry_too_few_items_rejected(self, schema):
        """Matrix entry with fewer than 4 items should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "external"]  # Missing noise
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_invalid_matrix_entry_too_many_items_rejected(self, schema):
        """Matrix entry with more than 4 items should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [
                ["Agent1", "Agent2", "external", 0.1, "extra"]
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_non_string_observer_rejected(self, schema):
        """Matrix entry with non-string observer should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [
                [123, "Agent2", "external", 0.1]
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_non_string_target_rejected(self, schema):
        """Matrix entry with non-string target should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [
                ["Agent1", 456, "external", 0.1]
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_default_missing_level_rejected(self, schema):
        """Default config missing 'level' field should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [],
            "default": {
                "noise": 0.15
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_default_missing_noise_rejected(self, schema):
        """Default config missing 'noise' field should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [],
            "default": {
                "level": "external"
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_default_negative_noise_rejected(self, schema):
        """Default config with negative noise should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [],
            "default": {
                "level": "external",
                "noise": -0.1
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_default_invalid_level_rejected(self, schema):
        """Default config with invalid level should be rejected."""
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": [],
                "internal": []
            },
            "matrix": [],
            "default": {
                "level": "invalid",
                "noise": 0.15
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)


class TestVariableOverlapValidation:
    """Tests for overlapping variables between external and internal lists.

    NOTE: The JSON schema does NOT enforce non-overlapping variables.
    This validation must be done at the application level (ObservabilityConfig).
    These tests document the expected behavior but will pass at schema level.
    """

    def test_overlapping_variables_passes_schema_validation(self, schema):
        """Overlapping external/internal variables pass JSON schema but should fail app-level validation.

        This test demonstrates that the JSON schema allows overlapping variables,
        but the application (ObservabilityConfig) must reject them.
        """
        config = {
            "enabled": True,
            "variable_visibility": {
                "external": ["var1", "var2"],
                "internal": ["var2", "var3"]  # var2 overlaps
            },
            "matrix": []
        }
        # JSON schema allows this - it doesn't check for overlaps
        validate(instance=config, schema=schema)

        # When ObservabilityConfig is implemented, it should raise:
        # ValidationError: "Variable 'var2' appears in both external and internal lists"
