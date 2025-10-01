"""Integration test for schema compatibility (Acceptance Scenario 6)."""

import pytest
import yaml
import json
from llm_sim.models.config import load_config
from llm_sim.orchestrator import Orchestrator
from llm_sim.persistence.checkpoint_manager import CheckpointManager
from llm_sim.models.exceptions import SchemaCompatibilityError


class TestSchemaCompatibility:
    def test_save_checkpoint_with_schema_x(self, tmp_path):
        """Save checkpoint with schema X."""
        config = {
            "simulation": {"name": "Test", "max_turns": 10},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"gdp": {"type": "float", "default": 1000.0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        loaded = load_config(config_path)
        orch = Orchestrator(loaded, output_dir=tmp_path)
        state = orch.initialize()

        mgr = CheckpointManager(output_dir=tmp_path, run_id="test")
        checkpoint_path = mgr.save(state, loaded)

        assert checkpoint_path.exists()
        return checkpoint_path

    def test_modify_config_to_schema_y_and_load(self, tmp_path):
        """Modify config to schema Y and attempt to load checkpoint."""
        # Save checkpoint with schema X
        config_x = {
            "simulation": {"name": "Test", "max_turns": 10},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"gdp": {"type": "float", "default": 1000.0}},
                "global_vars": {},
            },
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_x, f)

        loaded_x = load_config(config_path)
        orch = Orchestrator(loaded_x, output_dir=tmp_path)
        state = orch.initialize()

        mgr = CheckpointManager(output_dir=tmp_path, run_id="test")
        checkpoint_path = mgr.save(state, loaded_x)

        # Modify config to schema Y (different variables)
        config_y = {
            "simulation": {"name": "Test", "max_turns": 10},
            "engine": {"type": "economic"},
            "agents": [{"name": "Agent"}],
            "validator": {"type": "always_valid"},
            "state_variables": {
                "agent_vars": {"population": {"type": "int", "default": 1000000}},  # Different var
                "global_vars": {},
            },
        }

        with open(config_path, "w") as f:
            yaml.dump(config_y, f)

        loaded_y = load_config(config_path)

        # Attempt to load checkpoint with mismatched schema
        with pytest.raises(SchemaCompatibilityError) as exc_info:
            mgr.load(checkpoint_path, loaded_y)

        # Check error message explains mismatch
        error_msg = str(exc_info.value).lower()
        assert "schema" in error_msg or "mismatch" in error_msg or "compatibility" in error_msg
