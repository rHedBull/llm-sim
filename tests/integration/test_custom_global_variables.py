"""Integration test for custom global variables (Acceptance Scenario 2).

This test validates that custom global variables work end-to-end.
This test should FAIL until the feature is fully implemented.
"""

import pytest
import yaml
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator


class TestCustomGlobalVariables:
    """Integration test for Acceptance Scenario 2."""

    @pytest.fixture
    def custom_global_config(self, tmp_path):
        """Create config with custom global variables."""
        config = {
            "simulation": {"name": "Custom Global Test", "max_turns": 5},
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [{"name": "Nation_A", "type": "nation"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {},
                "global_vars": {
                    "inflation": {"type": "float", "min": -1.0, "max": 1.0, "default": 0.02},
                    "open_economy": {"type": "bool", "default": True},
                },
            },
        }

        config_path = tmp_path / "custom_global.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    def test_load_config_with_global_vars(self, custom_global_config):
        """Should load config with custom global variables."""
        config = load_config(custom_global_config)

        assert config.state_variables is not None
        assert "inflation" in config.state_variables.global_vars
        assert "open_economy" in config.state_variables.global_vars

    def test_initialize_simulation_with_custom_global_vars(self, custom_global_config):
        """Should initialize simulation with custom global variables."""
        config = load_config(custom_global_config)
        orchestrator = Orchestrator(config)

        state = orchestrator.initialize()

        # Check global state has custom variables
        assert hasattr(state.global_state, "inflation")
        assert hasattr(state.global_state, "open_economy")
        assert state.global_state.inflation == 0.02
        assert state.global_state.open_economy is True

    def test_global_state_has_custom_variables(self, custom_global_config):
        """Global state should have custom variables with correct types."""
        config = load_config(custom_global_config)
        orchestrator = Orchestrator(config)
        state = orchestrator.initialize()

        assert isinstance(state.global_state.inflation, float)
        assert isinstance(state.global_state.open_economy, bool)
