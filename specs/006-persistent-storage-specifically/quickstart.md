# Quickstart: Persistent Simulation State Storage

**Feature**: 006-persistent-storage-specifically
**Date**: 2025-10-01

## Overview

This guide demonstrates how to use the persistent state storage feature to:
1. Run simulations with automatic checkpoints
2. Resume simulations from saved checkpoints
3. Review saved results and historical states

## Prerequisites

- Completed implementation of persistence module
- Existing simulation configuration (YAML)
- Output directory is writable

## Scenario 1: Run Simulation with Checkpoints

### Configuration

Create `config_with_checkpoints.yaml`:
```yaml
simulation:
  name: "EconomicTest"
  max_turns: 15
  checkpoint_interval: 5  # Save every 5 turns
  termination:
    max_value: 10000
    min_value: 0

agents:
  - name: "Nation_A"
    type: "nation"
    initial_economic_strength: 1000.0

  - name: "Nation_B"
    type: "nation"
    initial_economic_strength: 1000.0

engine:
  type: "economic"
  interest_rate: 0.05

validator:
  type: "always_valid"
```

### Run Simulation

```bash
python main.py --config config_with_checkpoints.yaml
```

### Expected Output

```
Starting simulation: EconomicTest (2 agents)
Run ID: EconomicTest_2agents_20251001_143022_01

Turn 1: Processing...
Turn 5: Checkpoint saved (interval)
Turn 10: Checkpoint saved (interval)
Turn 15: Checkpoint saved (final)

Simulation complete!
Results saved to: output/EconomicTest_2agents_20251001_143022_01/result.json
```

### Verify Files

```bash
ls -R output/EconomicTest_2agents_20251001_143022_01/
```

Expected structure:
```
output/EconomicTest_2agents_20251001_143022_01/
├── checkpoints/
│   ├── last.json
│   ├── turn_5.json
│   ├── turn_10.json
│   └── turn_15.json
└── result.json
```

### Inspect Results

```bash
cat output/EconomicTest_2agents_20251001_143022_01/result.json
```

Should contain:
- Run metadata (run_id, start/end times)
- Final simulation state
- List of checkpoint turns: `[5, 10, 15]`
- Summary statistics

---

## Scenario 2: Resume from Checkpoint

### Run Partial Simulation

First, run a simulation but stop it early (or let it complete):
```bash
python main.py --config config_with_checkpoints.yaml
# Let it run to turn 10, checkpoint saved
```

### Resume from Turn 10

```bash
python main.py \
  --config config_with_checkpoints.yaml \
  --resume-from EconomicTest_2agents_20251001_143022_01 \
  --resume-turn 10
```

### Expected Behavior

```
Loading checkpoint: EconomicTest_2agents_20251001_143022_01/turn_10.json
Resuming from turn 10...

Turn 11: Processing...
Turn 15: Checkpoint saved (final)

Simulation complete!
```

### Validation

- New run ID generated (sequence incremented)
- Continues from turn 11 (next after loaded checkpoint)
- Final state matches as if run continuously

---

## Scenario 3: Multiple Concurrent Runs

### Start Two Simulations Simultaneously

Terminal 1:
```bash
python main.py --config config_with_checkpoints.yaml &
```

Terminal 2 (immediately):
```bash
python main.py --config config_with_checkpoints.yaml &
```

### Expected Behavior

- Run 1 gets ID: `EconomicTest_2agents_20251001_143022_01`
- Run 2 gets ID: `EconomicTest_2agents_20251001_143022_02` (sequence incremented)

### Verify

```bash
ls output/
```

Shows both directories:
```
EconomicTest_2agents_20251001_143022_01/
EconomicTest_2agents_20251001_143022_02/
```

---

## Scenario 4: Checkpoint Interval Disabled

### Configuration

Create `config_no_interval.yaml`:
```yaml
simulation:
  name: "QuickTest"
  max_turns: 20
  # checkpoint_interval omitted = disabled

agents:
  - name: "Agent_A"
    type: "nation"
    initial_economic_strength: 1000.0

engine:
  type: "economic"
  interest_rate: 0.05

validator:
  type: "always_valid"
```

### Run Simulation

```bash
python main.py --config config_no_interval.yaml
```

### Expected Behavior

- No interval checkpoints saved (turns 5, 10, 15 skipped)
- Only `last.json` updated each turn
- Final checkpoint saved at turn 20

### Verify

```bash
ls output/QuickTest_1agents_20251001_143500_01/checkpoints/
```

Shows:
```
last.json
turn_20.json  (final only)
```

---

## Scenario 5: Error Handling - Disk Full

### Simulate Disk Full

**(For testing only - requires mock/controlled environment)**

```python
# In test environment
import pytest
from unittest.mock import patch

def test_disk_full_handling():
    with patch('pathlib.Path.write_text', side_effect=OSError("No space left")):
        orchestrator = SimulationOrchestrator.from_yaml("config.yaml")

        with pytest.raises(CheckpointSaveError, match="No space left"):
            orchestrator.run()
```

### Expected Behavior

- Simulation halts immediately on save failure
- Clear error message displayed:
  ```
  CheckpointSaveError: Failed to save checkpoint at turn 5 to 'output/.../turn_5.json': No space left on device
  ```
- No partial/corrupted files written (atomic save pattern)
- Exit code 1

---

## Scenario 6: Load Corrupted Checkpoint

### Create Corrupted File

```bash
echo "{ invalid json }" > output/Test_1agents_20251001_120000_01/checkpoints/turn_5.json
```

### Attempt Resume

```bash
python main.py --resume-from Test_1agents_20251001_120000_01 --resume-turn 5
```

### Expected Behavior

```
CheckpointLoadError: Failed to load checkpoint from 'output/.../turn_5.json': Invalid JSON syntax
Simulation aborted.
```

Exit code 1

---

## Scenario 7: Inspect Checkpoint Contents

### Load Checkpoint Manually

```python
from pathlib import Path
from llm_sim.models.checkpoint import Checkpoint

checkpoint_path = Path("output/EconomicTest_2agents_20251001_143022_01/checkpoints/turn_10.json")
checkpoint = Checkpoint.model_validate_json(checkpoint_path.read_text())

print(f"Turn: {checkpoint.turn}")
print(f"Type: {checkpoint.checkpoint_type}")
print(f"Agents: {list(checkpoint.state.agents.keys())}")
print(f"Saved at: {checkpoint.timestamp}")
```

### Expected Output

```
Turn: 10
Type: interval
Agents: ['Nation_A', 'Nation_B']
Saved at: 2025-10-01 14:30:25.123456+00:00
```

---

## Integration Test Script

Automated test covering all scenarios:

```python
# tests/integration/test_persistent_storage_quickstart.py

def test_full_simulation_with_checkpoints(tmp_path):
    """Scenario 1: Run simulation, verify checkpoints."""
    config = create_test_config(checkpoint_interval=5, max_turns=15)
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    result = orchestrator.run()

    # Verify checkpoints created
    run_dir = tmp_path / result['run_id']
    assert (run_dir / "checkpoints" / "turn_5.json").exists()
    assert (run_dir / "checkpoints" / "turn_10.json").exists()
    assert (run_dir / "checkpoints" / "turn_15.json").exists()
    assert (run_dir / "result.json").exists()


def test_resume_from_checkpoint(tmp_path):
    """Scenario 2: Run simulation, resume from turn 10."""
    # First run
    config = create_test_config(checkpoint_interval=5, max_turns=15)
    orch1 = SimulationOrchestrator(config, output_root=tmp_path)
    result1 = orch1.run()
    run_id = result1['run_id']

    # Resume from turn 10
    orch2 = SimulationOrchestrator.from_checkpoint(
        run_id=run_id,
        turn=10,
        output_root=tmp_path
    )
    result2 = orch2.run()

    # Verify resumed correctly
    assert result2['final_state'].turn == 15
    assert result2['run_id'] != run_id  # New run ID


def test_concurrent_runs_unique_ids(tmp_path):
    """Scenario 3: Multiple concurrent runs get unique IDs."""
    config = create_test_config(max_turns=5)

    # Simulate concurrent starts (same timestamp)
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 10, 1, 12, 0, 0)

        orch1 = SimulationOrchestrator(config, output_root=tmp_path)
        result1 = orch1.run()

        orch2 = SimulationOrchestrator(config, output_root=tmp_path)
        result2 = orch2.run()

    # Verify unique IDs (sequence incremented)
    assert result1['run_id'].endswith('_01')
    assert result2['run_id'].endswith('_02')


def test_checkpoint_interval_disabled(tmp_path):
    """Scenario 4: No interval checkpoints when disabled."""
    config = create_test_config(checkpoint_interval=None, max_turns=20)
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    result = orchestrator.run()
    run_dir = tmp_path / result['run_id'] / "checkpoints"

    # Only final checkpoint (no intervals)
    checkpoints = list(run_dir.glob("turn_*.json"))
    assert len(checkpoints) == 1
    assert checkpoints[0].name == "turn_20.json"


def test_disk_full_error_handling(tmp_path):
    """Scenario 5: Simulation fails on disk full."""
    config = create_test_config(checkpoint_interval=5, max_turns=10)
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    with patch('pathlib.Path.write_text', side_effect=OSError("No space")):
        with pytest.raises(CheckpointSaveError, match="No space"):
            orchestrator.run()


def test_corrupted_checkpoint_error(tmp_path):
    """Scenario 6: Load fails on corrupted checkpoint."""
    # Create run with checkpoint
    config = create_test_config(checkpoint_interval=5, max_turns=10)
    orch = SimulationOrchestrator(config, output_root=tmp_path)
    result = orch.run()

    # Corrupt checkpoint
    checkpoint_file = tmp_path / result['run_id'] / "checkpoints" / "turn_5.json"
    checkpoint_file.write_text("{ invalid json }")

    # Attempt resume
    with pytest.raises(CheckpointLoadError):
        SimulationOrchestrator.from_checkpoint(
            run_id=result['run_id'],
            turn=5,
            output_root=tmp_path
        )
```

---

## Success Criteria

After running all scenarios:

✅ **Scenario 1**: Checkpoints saved at correct intervals
✅ **Scenario 2**: Simulation resumes from checkpoint, continues correctly
✅ **Scenario 3**: Concurrent runs have unique IDs
✅ **Scenario 4**: Interval checkpoints disabled when configured
✅ **Scenario 5**: Simulation fails fast on I/O errors
✅ **Scenario 6**: Clear error message on corrupted checkpoints
✅ **Scenario 7**: Checkpoint data inspectable and valid

## Troubleshooting

### Issue: "Permission denied" creating output directory
**Solution**: Ensure current directory is writable, or specify `--output-dir /path/to/writable`

### Issue: Checkpoint not found when resuming
**Solution**: Verify run ID matches exactly (case-sensitive), check turn number exists in checkpoints list

### Issue: Large checkpoint files slow down simulation
**Solution**: Increase checkpoint interval, or reduce agent count for testing

---

## Next Steps

- Implement remaining features (see tasks.md)
- Add CLI flags for resume functionality
- Document advanced usage (programmatic API)
- Add compression support for large checkpoints (future enhancement)
