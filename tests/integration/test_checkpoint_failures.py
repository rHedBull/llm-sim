"""Integration test for checkpoint failure handling."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    AgentConfig,
    ValidatorConfig,
)
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError
from llm_sim.persistence.checkpoint_manager import CheckpointManager


def create_test_config(checkpoint_interval=5):
    """Create a test simulation configuration."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="TestSim",
            max_turns=10,
            checkpoint_interval=checkpoint_interval,
        ),
        engine=EngineConfig(type="economic", interest_rate=0.05),
        agents=[
            AgentConfig(name="Agent1", type="nation", initial_economic_strength=1000.0),
        ],
        validator=ValidatorConfig(type="always_valid"),
    )


def test_disk_full_during_save(tmp_path):
    """Test: Simulate disk full during save."""
    config = create_test_config(checkpoint_interval=5)

    # Mock the save operation to raise OSError
    with patch("llm_sim.persistence.storage.JSONStorage.save_json", side_effect=OSError("No space left on device")):
        orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

        # Simulation should raise CheckpointSaveError when trying to save checkpoint
        with pytest.raises(CheckpointSaveError, match="No space left on device"):
            orchestrator.run()


def test_corrupt_checkpoint_file(tmp_path, legacy_variable_definitions):
    """Test: Corrupt checkpoint file, attempt resume."""
    # Create a checkpoint manager and simulate a corrupted file
    agent_var_defs, global_var_defs = legacy_variable_definitions
    manager = CheckpointManager(
        run_id="test_run_01",
        agent_var_defs=agent_var_defs,
        global_var_defs=global_var_defs,
        checkpoint_interval=5,
        output_root=tmp_path
    )

    # Create a corrupted checkpoint file
    checkpoint_dir = tmp_path / "test_run_01" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "turn_5.json").write_text("{ invalid json }")

    # Attempt to load should raise CheckpointLoadError
    with pytest.raises(CheckpointLoadError, match="Invalid JSON|Schema validation failed|Failed to load"):
        manager.load_checkpoint("test_run_01", 5)


def test_permission_denied_on_directory_creation(tmp_path):
    """Test: Permission denied when creating checkpoint directory."""
    config = create_test_config(checkpoint_interval=5)

    # Mock mkdir to raise PermissionError
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
        # Should raise CheckpointSaveError when trying to create directory
        with pytest.raises(CheckpointSaveError, match="Permission denied"):
            orchestrator = SimulationOrchestrator(config, output_root=tmp_path)
