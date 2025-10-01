"""Integration test for checkpoint persistence (Acceptance Scenario 3).

This test validates that checkpoints preserve custom variables.
This test should FAIL until the feature is fully implemented.
"""

import pytest
import yaml
import json
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator
from llm_sim.persistence.checkpoint_manager import CheckpointManager


class TestCheckpointCustomVars:
    """Integration test for Acceptance Scenario 3."""

    @pytest.fixture
    def checkpoint_config(self, tmp_path):
        """Create config with custom variables for checkpoint testing."""
        config = {
            "simulation": {"name": "Checkpoint Test", "max_turns": 10, "checkpoint_interval": 5},
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [{"name": "Nation_A", "type": "nation"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {
                    "gdp": {"type": "float", "min": 0, "default": 1000.0},
                    "population": {"type": "int", "min": 1, "default": 1000000},
                },
                "global_vars": {
                    "inflation": {"type": "float", "min": -1.0, "max": 1.0, "default": 0.02},
                    "open_economy": {"type": "bool", "default": True},
                },
            },
        }

        config_path = tmp_path / "checkpoint.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    def test_run_simulation_with_custom_variables(self, checkpoint_config, tmp_path):
        """Should run simulation with custom variables."""
        config = load_config(checkpoint_config)
        orchestrator = Orchestrator(config, output_root=tmp_path)

        state = orchestrator.initialize()

        # Run a few turns using internal methods
        for _ in range(5):
            state = orchestrator._run_turn_sync(state)

        assert state.turn == 5

    def test_create_checkpoint_with_custom_vars(self, checkpoint_config, tmp_path):
        """Should create checkpoint containing custom variables."""
        config = load_config(checkpoint_config)
        orchestrator = Orchestrator(config, output_root=tmp_path)

        state = orchestrator.initialize()

        # Create checkpoint using orchestrator's checkpoint manager
        checkpoint_path = orchestrator.checkpoint_manager.save_checkpoint(state, "interval")

        # Verify checkpoint exists
        assert checkpoint_path.exists()

    def test_checkpoint_contains_all_custom_agent_variables(self, checkpoint_config, tmp_path):
        """Checkpoint should contain all custom agent variables."""
        config = load_config(checkpoint_config)
        orchestrator = Orchestrator(config, output_root=tmp_path)

        state = orchestrator.initialize()

        checkpoint_path = orchestrator.checkpoint_manager.save_checkpoint(state, "interval")

        # Load and inspect checkpoint
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)

        agent_state = checkpoint["state"]["agents"]["Nation_A"]
        assert "gdp" in agent_state
        assert "population" in agent_state

    def test_checkpoint_contains_all_custom_global_variables(self, checkpoint_config, tmp_path):
        """Checkpoint should contain all custom global variables."""
        config = load_config(checkpoint_config)
        orchestrator = Orchestrator(config, output_root=tmp_path)

        state = orchestrator.initialize()

        checkpoint_path = orchestrator.checkpoint_manager.save_checkpoint(state, "interval")

        # Load and inspect checkpoint
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)

        global_state = checkpoint["state"]["global_state"]
        assert "inflation" in global_state
        assert "open_economy" in global_state

    def test_checkpoint_metadata_includes_schema_hash(self, checkpoint_config, tmp_path):
        """Checkpoint metadata should include schema_hash."""
        config = load_config(checkpoint_config)
        orchestrator = Orchestrator(config, output_root=tmp_path)

        state = orchestrator.initialize()

        checkpoint_path = orchestrator.checkpoint_manager.save_checkpoint(state, "interval")

        # Load and inspect checkpoint
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)

        assert "schema_hash" in checkpoint["metadata"]
        assert len(checkpoint["metadata"]["schema_hash"]) == 64  # SHA-256 hex
