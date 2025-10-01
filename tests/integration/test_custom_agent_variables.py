"""Integration test for custom agent variables (Acceptance Scenario 1).

This test validates that custom agent variables work end-to-end.
This test should FAIL until the feature is fully implemented.
"""

import pytest
import yaml
from pathlib import Path
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator


class TestCustomAgentVariables:
    """Integration test for Acceptance Scenario 1."""

    @pytest.fixture
    def custom_agent_config(self, tmp_path):
        """Create config with custom agent variables."""
        config = {
            "simulation": {"name": "Custom Agent Test", "max_turns": 5},
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation_A", "type": "nation"},
                {"name": "Nation_B", "type": "nation"},
            ],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {
                    "gdp": {"type": "float", "min": 0, "max": 1000000, "default": 1000.0},
                    "population": {"type": "int", "min": 1, "default": 1000000},
                },
                "global_vars": {},
            },
        }

        config_path = tmp_path / "custom_agent.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    def test_load_config_with_agent_vars(self, custom_agent_config):
        """Should load config with custom agent variables."""
        config = load_config(custom_agent_config)

        assert config.state_variables is not None
        assert "gdp" in config.state_variables.agent_vars
        assert "population" in config.state_variables.agent_vars

    def test_initialize_simulation_with_custom_agent_vars(self, custom_agent_config):
        """Should initialize simulation with custom agent variables."""
        config = load_config(custom_agent_config)
        orchestrator = Orchestrator(config)

        # Initialize simulation
        state = orchestrator.initialize()

        # Check agent states have custom variables
        assert "Nation_A" in state.agents
        assert "Nation_B" in state.agents

        agent_a = state.agents["Nation_A"]
        assert hasattr(agent_a, "gdp")
        assert hasattr(agent_a, "population")
        assert agent_a.gdp == 1000.0
        assert agent_a.population == 1000000

    def test_agent_states_have_custom_variables_with_correct_types(self, custom_agent_config):
        """Agent states should have variables with correct types."""
        config = load_config(custom_agent_config)
        orchestrator = Orchestrator(config)
        state = orchestrator.initialize()

        agent = state.agents["Nation_A"]

        assert isinstance(agent.gdp, float)
        assert isinstance(agent.population, int)

    def test_no_hardcoded_economic_strength_field_present(self, custom_agent_config):
        """Should NOT have hardcoded 'economic_strength' field."""
        config = load_config(custom_agent_config)
        orchestrator = Orchestrator(config)
        state = orchestrator.initialize()

        agent = state.agents["Nation_A"]

        # economic_strength should NOT be present
        assert not hasattr(agent, "economic_strength")
