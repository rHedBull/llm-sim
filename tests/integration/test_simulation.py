"""Integration tests for programmatic simulation orchestration."""

import pytest

from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.models.config import SimulationConfig


class TestSimulationOrchestration:
    """Integration tests for programmatic simulation execution."""

    def test_basic_simulation_run(self) -> None:
        """Test running a basic simulation."""
        config_data = {
            "simulation": {
                "name": "Test Simulation",
                "max_turns": 5,
                "termination": {"min_value": 0.0, "max_value": 10000.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Nation_B", "type": "nation", "initial_economic_strength": 1500.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config)

        result = orchestrator.run()

        assert result is not None
        assert "final_state" in result
        assert "history" in result
        assert "stats" in result

        final_state = result["final_state"]
        assert final_state.turn == 5
        assert len(final_state.agents) == 2
        # Check growth (1000 * 1.05^5 ≈ 1276.28)
        assert final_state.agents["Nation_A"].economic_strength > 1250
        assert final_state.agents["Nation_A"].economic_strength < 1300

        history = result["history"]
        assert len(history) == 6  # Initial + 5 turns

    def test_early_termination_max_value(self) -> None:
        """Test early termination by max value."""
        config_data = {
            "simulation": {
                "name": "Test Max Value",
                "max_turns": 100,
                "termination": {"max_value": 3000.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.5},  # High growth
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Nation_B", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config)

        result = orchestrator.run()

        final_state = result["final_state"]
        assert final_state.turn < 100  # Should terminate early
        assert final_state.global_state.total_economic_value > 3000.0

    def test_early_termination_min_value(self) -> None:
        """Test early termination by min value."""
        config_data = {
            "simulation": {
                "name": "Test Min Value",
                "max_turns": 100,
                "termination": {"min_value": 500.0},
            },
            "engine": {"type": "economic", "interest_rate": -0.5},  # Negative growth
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config)

        result = orchestrator.run()

        final_state = result["final_state"]
        assert final_state.turn < 100  # Should terminate early
        assert final_state.global_state.total_economic_value < 500.0

    def test_different_agent_strategies(self) -> None:
        """Test simulation with different agent strategies."""
        config_data = {
            "simulation": {
                "name": "Mixed Strategies",
                "max_turns": 3,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.1},
            "agents": [
                {"name": "Grower", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Maintainer", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Decliner", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)

        # Create orchestrator with custom agent strategies
        orchestrator = SimulationOrchestrator(
            config,
            agent_strategies={"Grower": "grow", "Maintainer": "maintain", "Decliner": "decline"},
        )

        result = orchestrator.run()

        final_state = result["final_state"]
        # All should grow equally due to engine interest rate
        assert final_state.agents["Grower"].economic_strength == pytest.approx(1331.0, rel=1e-2)
        assert final_state.agents["Maintainer"].economic_strength == pytest.approx(1331.0, rel=1e-2)
        assert final_state.agents["Decliner"].economic_strength == pytest.approx(1331.0, rel=1e-2)


    def test_validation_statistics(self) -> None:
        """Test that validation statistics are tracked."""
        config_data = {
            "simulation": {
                "name": "Stats Test",
                "max_turns": 10,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.01},
            "agents": [
                {"name": "Agent1", "type": "nation", "initial_economic_strength": 100.0},
                {"name": "Agent2", "type": "nation", "initial_economic_strength": 100.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config)

        result = orchestrator.run()

        stats = result["stats"]
        assert "validation" in stats
        assert stats["validation"]["total_validated"] == 20  # 2 agents * 10 turns
        assert stats["validation"]["total_rejected"] == 0
        assert stats["validation"]["acceptance_rate"] == 1.0
