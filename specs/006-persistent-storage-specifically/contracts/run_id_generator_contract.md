# Contract: RunIDGenerator

**Component**: `src/llm_sim/persistence/run_id_generator.py`
**Purpose**: Generates unique run identifiers
**Type**: Utility

## Interface

```python
from datetime import datetime
from pathlib import Path

class RunIDGenerator:
    """Generates unique run identifiers for simulations."""

    @staticmethod
    def generate(
        simulation_name: str,
        num_agents: int,
        start_time: datetime,
        output_root: Path = Path("output")
    ) -> str:
        """Generate unique run ID with collision detection.

        Args:
            simulation_name: Name from config
            num_agents: Number of agents
            start_time: Simulation start time
            output_root: Output directory for collision checking

        Returns:
            Unique run ID: {name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}

        Raises:
            RunIDCollisionError: If collision cannot be resolved
        """
        ...
```

## Contract Tests

**File**: `tests/contract/test_run_id_generator_contract.py`

### Test 1: Format Validation
```python
def test_generate_format():
    """Generated ID matches expected format."""
    run_id = RunIDGenerator.generate(
        simulation_name="EconomicTest",
        num_agents=3,
        start_time=datetime(2025, 10, 1, 14, 30, 22),
        output_root=Path("/tmp/test")
    )

    pattern = r"^EconomicTest_3agents_20251001_143022_\d{2}$"
    assert re.match(pattern, run_id)
```

### Test 2: Sequence Increment on Collision
```python
def test_generate_increments_sequence(tmp_path):
    """Increments sequence number when directory exists."""
    # Create existing directory
    (tmp_path / "Test_2agents_20251001_120000_01").mkdir(parents=True)

    run_id = RunIDGenerator.generate(
        "Test", 2, datetime(2025, 10, 1, 12, 0, 0), tmp_path
    )

    assert run_id == "Test_2agents_20251001_120000_02"
```

### Test 3: Handles Special Characters
```python
def test_generate_sanitizes_name():
    """Sanitizes special characters in simulation name."""
    run_id = RunIDGenerator.generate(
        "Test/With Spaces",
        2,
        datetime(2025, 10, 1, 12, 0, 0)
    )

    assert "/" not in run_id
    assert " " not in run_id or run_id.count("_") > 3  # Spaces → underscores
```

### Test 4: Collision Limit
```python
def test_generate_raises_on_too_many_collisions(tmp_path):
    """Raises error if sequence exceeds 99."""
    # Create directories 01-99
    for seq in range(1, 100):
        (tmp_path / f"Test_2agents_20251001_120000_{seq:02d}").mkdir(parents=True)

    with pytest.raises(RunIDCollisionError):
        RunIDGenerator.generate("Test", 2, datetime(2025, 10, 1, 12, 0, 0), tmp_path)
```

## Behavior Specifications

- **Format**: `{name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}`
- **Sequence**: Two-digit zero-padded (01-99)
- **Collision**: Checks filesystem, increments until unique
- **Sanitization**: Replaces `/` and spaces with `_`
- **Limit**: Max 99 concurrent runs per second
