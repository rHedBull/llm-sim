# Contract: CheckpointManager

**Component**: `src/llm_sim/persistence/checkpoint_manager.py`
**Purpose**: Manages checkpoint saving and loading operations
**Type**: Core service

## Interface

```python
from pathlib import Path
from llm_sim.models.state import SimulationState
from llm_sim.models.checkpoint import SimulationResults

class CheckpointManager:
    """Manages simulation checkpoint operations."""

    def __init__(
        self,
        run_id: str,
        checkpoint_interval: int | None,
        output_root: Path = Path("output")
    ):
        """Initialize checkpoint manager for a simulation run.

        Args:
            run_id: Unique run identifier
            checkpoint_interval: Save every N turns (None = disabled)
            output_root: Root directory for output files
        """
        ...

    def should_save_checkpoint(self, turn: int, is_final: bool) -> bool:
        """Determine if checkpoint should be saved at this turn.

        Args:
            turn: Current turn number
            is_final: True if this is the last turn

        Returns:
            True if checkpoint should be saved
        """
        ...

    def save_checkpoint(
        self,
        state: SimulationState,
        checkpoint_type: Literal["interval", "last", "final"]
    ) -> Path:
        """Save simulation state checkpoint.

        Args:
            state: Complete simulation state
            checkpoint_type: Type of checkpoint

        Returns:
            Path to saved checkpoint file

        Raises:
            CheckpointSaveError: If save fails for any reason
        """
        ...

    def load_checkpoint(self, run_id: str, turn: int) -> SimulationState:
        """Load checkpoint from disk.

        Args:
            run_id: Run identifier
            turn: Turn number to load (or "last" for most recent)

        Returns:
            SimulationState from checkpoint

        Raises:
            CheckpointLoadError: If load fails or file not found
        """
        ...

    def list_checkpoints(self, run_id: str) -> list[int]:
        """List available checkpoint turns for a run.

        Args:
            run_id: Run identifier

        Returns:
            Sorted list of turn numbers with checkpoints

        Raises:
            CheckpointLoadError: If run directory not found
        """
        ...

    def save_results(self, results: SimulationResults) -> Path:
        """Save final simulation results.

        Args:
            results: Complete simulation results

        Returns:
            Path to result.json file

        Raises:
            CheckpointSaveError: If save fails
        """
        ...
```

## Contract Tests

**File**: `tests/contract/test_checkpoint_manager_contract.py`

### Test 1: Initialization
```python
def test_checkpoint_manager_init():
    """Manager initializes with run ID and interval."""
    manager = CheckpointManager(
        run_id="Test_2agents_20251001_120000_01",
        checkpoint_interval=10
    )
    assert manager.run_id == "Test_2agents_20251001_120000_01"
    assert manager.checkpoint_interval == 10
```

### Test 2: Should Save at Interval
```python
def test_should_save_checkpoint_at_interval():
    """Returns True at checkpoint intervals."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5)

    assert manager.should_save_checkpoint(turn=5, is_final=False) is True
    assert manager.should_save_checkpoint(turn=10, is_final=False) is True
    assert manager.should_save_checkpoint(turn=3, is_final=False) is False
    assert manager.should_save_checkpoint(turn=7, is_final=False) is False
```

### Test 3: Should Save Final
```python
def test_should_save_checkpoint_final():
    """Always saves final turn regardless of interval."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=10)

    assert manager.should_save_checkpoint(turn=15, is_final=True) is True
    assert manager.should_save_checkpoint(turn=3, is_final=True) is True
```

### Test 4: Should Save When Interval Disabled
```python
def test_should_save_checkpoint_no_interval():
    """Only saves final when interval is None."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=None)

    assert manager.should_save_checkpoint(turn=5, is_final=False) is False
    assert manager.should_save_checkpoint(turn=10, is_final=False) is False
    assert manager.should_save_checkpoint(turn=10, is_final=True) is True
```

### Test 5: Save Checkpoint Creates File
```python
def test_save_checkpoint_creates_file(tmp_path):
    """Saves checkpoint to correct file path."""
    manager = CheckpointManager(
        "test_run_01",
        checkpoint_interval=5,
        output_root=tmp_path
    )

    state = create_test_state(turn=5)
    path = manager.save_checkpoint(state, checkpoint_type="interval")

    assert path.exists()
    assert path == tmp_path / "test_run_01" / "checkpoints" / "turn_5.json"
```

### Test 6: Save Checkpoint Validates Content
```python
def test_save_checkpoint_roundtrip(tmp_path):
    """Saved checkpoint can be loaded back."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    original_state = create_test_state(turn=10)
    manager.save_checkpoint(original_state, checkpoint_type="interval")

    loaded_state = manager.load_checkpoint("test_run_01", turn=10)

    assert loaded_state.turn == original_state.turn
    assert loaded_state.agents == original_state.agents
```

### Test 7: Save Checkpoint Fails on I/O Error
```python
def test_save_checkpoint_raises_on_error(tmp_path):
    """Raises CheckpointSaveError on I/O failure."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    # Make directory read-only
    run_dir = tmp_path / "test_run_01"
    run_dir.mkdir(parents=True)
    run_dir.chmod(0o444)

    state = create_test_state(turn=5)

    with pytest.raises(CheckpointSaveError):
        manager.save_checkpoint(state, checkpoint_type="interval")
```

### Test 8: Load Checkpoint Returns State
```python
def test_load_checkpoint_success(tmp_path):
    """Loads checkpoint and returns SimulationState."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    original = create_test_state(turn=10)
    manager.save_checkpoint(original, checkpoint_type="interval")

    loaded = manager.load_checkpoint("test_run_01", turn=10)

    assert isinstance(loaded, SimulationState)
    assert loaded.turn == 10
```

### Test 9: Load Checkpoint Raises on Missing File
```python
def test_load_checkpoint_missing_file(tmp_path):
    """Raises CheckpointLoadError when file not found."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    with pytest.raises(CheckpointLoadError, match="not found"):
        manager.load_checkpoint("test_run_01", turn=99)
```

### Test 10: Load Checkpoint Raises on Corrupted File
```python
def test_load_checkpoint_corrupted_file(tmp_path):
    """Raises CheckpointLoadError on invalid JSON."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    # Create corrupted checkpoint file
    checkpoint_dir = tmp_path / "test_run_01" / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    corrupt_file = checkpoint_dir / "turn_5.json"
    corrupt_file.write_text("{ invalid json }")

    with pytest.raises(CheckpointLoadError):
        manager.load_checkpoint("test_run_01", turn=5)
```

### Test 11: List Checkpoints Returns Sorted
```python
def test_list_checkpoints(tmp_path):
    """Returns sorted list of available checkpoint turns."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    # Save checkpoints
    for turn in [5, 15, 10]:
        state = create_test_state(turn=turn)
        manager.save_checkpoint(state, checkpoint_type="interval")

    checkpoints = manager.list_checkpoints("test_run_01")

    assert checkpoints == [5, 10, 15]  # Sorted
```

### Test 12: Save Results Creates File
```python
def test_save_results(tmp_path):
    """Saves results to result.json."""
    manager = CheckpointManager("test_run_01", checkpoint_interval=5, output_root=tmp_path)

    results = create_test_results()
    path = manager.save_results(results)

    assert path.exists()
    assert path == tmp_path / "test_run_01" / "result.json"
```

## Behavior Specifications

### Checkpoint Naming
- `interval` type → `checkpoints/turn_{N}.json`
- `last` type → `checkpoints/last.json` (overwrites)
- `final` type → `checkpoints/turn_{N}.json`

### Directory Creation
- Creates `output/{run_id}/checkpoints/` automatically
- Idempotent (safe to call multiple times)
- Raises `CheckpointSaveError` on permission denied

### Atomic Writes
- All saves use temp file + rename pattern
- Ensures no partial writes on interruption
- Uses `Path.replace()` for cross-platform atomicity

### Error Handling
- I/O errors → `CheckpointSaveError` with context
- JSON decode errors → `CheckpointLoadError` with context
- Missing files → `CheckpointLoadError` with "not found" message
- Permission errors → converted to appropriate exception

## Dependencies

- `src/llm_sim/persistence/storage.py` (JSONStorage)
- `src/llm_sim/models/checkpoint.py` (Checkpoint, SimulationResults)
- `src/llm_sim/models/state.py` (SimulationState)

## Performance Requirements

- `save_checkpoint()`: <1s for typical state (100 agents)
- `load_checkpoint()`: <500ms for typical state
- `list_checkpoints()`: <100ms (filesystem scan)
