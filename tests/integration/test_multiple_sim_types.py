"""Integration test for multiple simulation types (Acceptance Scenario 4)."""

import pytest
import yaml
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator


class TestMultipleSimTypes:
    def test_economic_simulation_with_econ_variables(self, tmp_path):
        """Economic simulation should track economic variables only."""
        config = {
            "simulation": {"name": "Economic", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Nation_A", "type": "nation"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"gdp": {"type": "float", "default": 1000.0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "economic.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        loaded = load_config(config_path)
        orch = Orchestrator(loaded)
        state = orch.initialize()

        assert hasattr(state.agents["Nation_A"], "gdp")
        assert not hasattr(state.agents["Nation_A"], "army_size")

    def test_military_simulation_with_military_variables(self, tmp_path):
        """Military simulation should track military variables only."""
        config = {
            "simulation": {"name": "Military", "max_turns": 5},
            "engine": {"type": "economic"},
            "agents": [{"name": "Empire_A", "type": "nation"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"army_size": {"type": "int", "min": 0, "default": 1000}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "military.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        loaded = load_config(config_path)
        orch = Orchestrator(loaded)
        state = orch.initialize()

        assert hasattr(state.agents["Empire_A"], "army_size")
        assert not hasattr(state.agents["Empire_A"], "gdp")
