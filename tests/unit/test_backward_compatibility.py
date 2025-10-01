"""Unit tests for backward compatibility defaults.

These tests validate that configs without state_variables use default variables.
These tests should FAIL until backward compatibility is implemented.
"""

import pytest
from llm_sim.models.config import SimulationConfig, get_variable_definitions
import structlog


class TestBackwardCompatibilityDefaults:
    """Tests for backward compatibility with legacy configs."""

    def test_config_without_state_variables_uses_defaults(self):
        """Config without state_variables should use implicit defaults."""
        config = SimulationConfig(
            simulation={"name": "Test", "max_turns": 10},
            engine={"type": "economic"},
            agents=[{"name": "Agent1"}],
            validator={"type": "always_valid"},
            # NO state_variables field
        )

        agent_vars, global_vars = get_variable_definitions(config)

        # Should have default variables
        assert "economic_strength" in agent_vars
        assert agent_vars["economic_strength"].type == "float"
        assert agent_vars["economic_strength"].min == 0

    def test_default_agent_vars_include_economic_strength(self):
        """Default agent vars should include economic_strength."""
        config = SimulationConfig(
            simulation={"name": "Test", "max_turns": 10},
            engine={"type": "economic"},
            agents=[{"name": "Agent1"}],
            validator={"type": "always_valid"},
        )

        agent_vars, global_vars = get_variable_definitions(config)

        assert "economic_strength" in agent_vars
        assert agent_vars["economic_strength"].default == 0.0

    def test_default_global_vars_include_legacy_fields(self):
        """Default global vars should include legacy economic fields."""
        config = SimulationConfig(
            simulation={"name": "Test", "max_turns": 10},
            engine={"type": "economic"},
            agents=[{"name": "Agent1"}],
            validator={"type": "always_valid"},
        )

        agent_vars, global_vars = get_variable_definitions(config)

        # Should have legacy global variables
        assert "interest_rate" in global_vars
        assert "total_economic_value" in global_vars
        assert "gdp_growth" in global_vars
        assert "inflation" in global_vars
        assert "unemployment" in global_vars

    def test_deprecation_warning_is_logged(self, caplog):
        """Should log deprecation warning when using defaults."""
        with caplog.at_level("WARNING"):
            config = SimulationConfig(
                simulation={"name": "Test", "max_turns": 10},
                engine={"type": "economic"},
                agents=[{"name": "Agent1"}],
                validator={"type": "always_valid"},
            )

            get_variable_definitions(config)

            # Check for deprecation warning
            assert any("state_variables" in record.message for record in caplog.records)
            assert any("legacy" in record.message.lower() for record in caplog.records)

    def test_explicit_state_variables_no_warning(self, caplog):
        """Should NOT log warning when state_variables is explicit."""
        from llm_sim.models.config import StateVariablesConfig, VariableDefinition

        with caplog.at_level("WARNING"):
            config = SimulationConfig(
                simulation={"name": "Test", "max_turns": 10},
                engine={"type": "economic"},
                agents=[{"name": "Agent1"}],
                validator={"type": "always_valid"},
                state_variables=StateVariablesConfig(
                    agent_vars={"gdp": VariableDefinition(type="float", default=1000.0)},
                    global_vars={},
                ),
            )

            get_variable_definitions(config)

            # Should NOT have deprecation warning
            assert not any("legacy" in record.message.lower() for record in caplog.records)
