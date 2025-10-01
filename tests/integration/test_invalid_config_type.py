"""Integration test for invalid config type (Acceptance Scenario 7)."""

import pytest
import yaml
from pydantic import ValidationError
from llm_sim.models.config import load_config
from llm_sim.models.exceptions import ConfigValidationError


class TestInvalidConfigType:
    def test_create_config_with_unsupported_type(self, tmp_path):
        """Config with unsupported type should fail validation."""
        config = {
            "simulation": {"name": "Test", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"value": {"type": "complex_number", "default": 0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "bad.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        # Should raise validation error
        with pytest.raises((ValidationError, ConfigValidationError)) as exc_info:
            load_config(config_path)

        error_msg = str(exc_info.value).lower()
        assert "complex_number" in error_msg or "type" in error_msg

    def test_error_lists_supported_types(self, tmp_path):
        """Error message should list supported types."""
        config = {
            "simulation": {"name": "Test", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"value": {"type": "invalid", "default": 0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "bad.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        with pytest.raises((ValidationError, ConfigValidationError)) as exc_info:
            load_config(config_path)

        error_msg = str(exc_info.value).lower()
        # Should mention supported types
        assert "float" in error_msg or "int" in error_msg or "bool" in error_msg
