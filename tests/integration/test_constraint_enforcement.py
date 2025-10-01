"""Integration test for constraint enforcement (Acceptance Scenario 5)."""

import pytest
import yaml
from pydantic import ValidationError
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator


class TestConstraintEnforcement:
    def test_define_variable_with_min_max_constraints(self, tmp_path):
        """Should define variable with constraints."""
        config = {
            "simulation": {"name": "Test", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"value": {"type": "float", "min": 0, "max": 100, "default": 50.0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "test.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        loaded = load_config(config_path)
        orch = Orchestrator(loaded)
        state = orch.initialize()

        assert state.agents["Agent"].value == 50.0

    def test_attempt_update_exceeding_max(self, tmp_path):
        """Should reject value exceeding max."""
        config = {
            "simulation": {"name": "Test", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"value": {"type": "float", "min": 0, "max": 100, "default": 50.0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "test.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        loaded = load_config(config_path)
        orch = Orchestrator(loaded)
        state = orch.initialize()

        agent = state.agents["Agent"]

        # Attempt to update with value > max
        with pytest.raises(ValidationError) as exc_info:
            agent.model_copy(update={"value": 150.0})

        # Check error message is clear
        assert "150" in str(exc_info.value) or "max" in str(exc_info.value).lower()
