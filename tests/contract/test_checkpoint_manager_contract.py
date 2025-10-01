"""Contract tests for CheckpointManager."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from llm_sim.persistence.checkpoint_manager import CheckpointManager
from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError
from llm_sim.models.state import SimulationState, create_global_state_model
from llm_sim.models.checkpoint import SimulationResults
from llm_sim.models.config import VariableDefinition


@pytest.fixture
def test_var_defs():
    """Test variable definitions for checkpoint manager."""
    agent_vars = {"economic_strength": VariableDefinition(type="float", min=0, default=0.0)}
    global_vars = {"interest_rate": VariableDefinition(type="float", default=0.05)}
    return agent_vars, global_vars


def create_test_state(turn: int) -> SimulationState:
    """Create a test simulation state."""
    global_vars = {"interest_rate": VariableDefinition(type="float", default=0.05)}
    GlobalState = create_global_state_model(global_vars)
    return SimulationState(
        turn=turn,
        agents={},
        global_state=GlobalState(interest_rate=0.05)
    )


def test_should_save_checkpoint_returns_true_at_intervals(tmp_path, test_var_defs):
    """Test should_save_checkpoint returns True at intervals."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    assert manager.should_save_checkpoint(5, is_final=False) is True
    assert manager.should_save_checkpoint(10, is_final=False) is True
    assert manager.should_save_checkpoint(3, is_final=False) is False


def test_should_save_checkpoint_always_true_for_final(tmp_path, test_var_defs):
    """Test should_save_checkpoint always True for final turn."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    assert manager.should_save_checkpoint(7, is_final=True) is True
    assert manager.should_save_checkpoint(100, is_final=True) is True


def test_should_save_checkpoint_respects_disabled_interval(tmp_path, test_var_defs):
    """Test should_save_checkpoint respects disabled interval (None)."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=None, output_root=tmp_path)

    assert manager.should_save_checkpoint(5, is_final=False) is False
    assert manager.should_save_checkpoint(10, is_final=False) is False
    assert manager.should_save_checkpoint(5, is_final=True) is True


def test_save_checkpoint_creates_file_at_correct_path(tmp_path, test_var_defs):
    """Test save_checkpoint creates file at correct path."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)
    state = create_test_state(5)

    path = manager.save_checkpoint(state, "interval")

    expected_path = tmp_path / "test_run_01" / "checkpoints" / "turn_5.json"
    assert path == expected_path
    assert path.exists()


def test_save_checkpoint_validates_content_roundtrip(tmp_path, test_var_defs):
    """Test save_checkpoint validates content round-trip."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)
    state = create_test_state(5)

    save_path = manager.save_checkpoint(state, "interval")
    loaded_state = manager.load_checkpoint("test_run_01", 5)

    assert loaded_state.turn == state.turn


def test_save_checkpoint_raises_on_io_failure(tmp_path, test_var_defs):
    """Test save_checkpoint raises CheckpointSaveError on I/O failure."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)
    state = create_test_state(5)

    with patch("llm_sim.persistence.storage.JSONStorage.save_json", side_effect=OSError("Disk full")):
        with pytest.raises(CheckpointSaveError, match="Disk full"):
            manager.save_checkpoint(state, "interval")


def test_load_checkpoint_returns_simulation_state(tmp_path, test_var_defs):
    """Test load_checkpoint returns SimulationState."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)
    state = create_test_state(5)
    manager.save_checkpoint(state, "interval")

    loaded_state = manager.load_checkpoint("test_run_01", 5)

    assert isinstance(loaded_state, SimulationState)
    assert loaded_state.turn == 5


def test_load_checkpoint_raises_on_missing_file(tmp_path, test_var_defs):
    """Test load_checkpoint raises CheckpointLoadError on missing file."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    with pytest.raises(CheckpointLoadError):
        manager.load_checkpoint("test_run_01", 5)


def test_load_checkpoint_raises_on_corrupted_file(tmp_path, test_var_defs):
    """Test load_checkpoint raises CheckpointLoadError on corrupted file."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    # Create corrupted checkpoint file (directory already exists from manager init)
    checkpoint_dir = tmp_path / "test_run_01" / "checkpoints"
    (checkpoint_dir / "turn_5.json").write_text("{ invalid json }")

    with pytest.raises(CheckpointLoadError):
        manager.load_checkpoint("test_run_01", 5)


def test_list_checkpoints_returns_sorted_list(tmp_path, test_var_defs):
    """Test list_checkpoints returns sorted list of available turns."""
    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    # Save checkpoints at different turns
    manager.save_checkpoint(create_test_state(10), "interval")
    manager.save_checkpoint(create_test_state(5), "interval")
    manager.save_checkpoint(create_test_state(15), "final")

    checkpoints = manager.list_checkpoints("test_run_01")

    assert checkpoints == [5, 10, 15]


def test_save_results_creates_result_json(tmp_path, test_var_defs):
    """Test save_results creates result.json file."""
    from llm_sim.models.checkpoint import RunMetadata
    from datetime import datetime

    agent_vars, global_vars = test_var_defs
    manager = CheckpointManager("test_run_01", agent_vars, global_vars, checkpoint_interval=5, output_root=tmp_path)

    results = SimulationResults(
        run_metadata=RunMetadata(
            run_id="test_run_01",
            simulation_name="Test",
            num_agents=2,
            start_time=datetime.now(),
            end_time=datetime.now(),
            checkpoint_interval=5,
            config_snapshot={}
        ),
        final_state=create_test_state(15),
        checkpoints=[5, 10, 15],
        summary_stats={}
    )

    path = manager.save_results(results)

    expected_path = tmp_path / "test_run_01" / "result.json"
    assert path == expected_path
    assert path.exists()
