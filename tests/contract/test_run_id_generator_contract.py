"""Contract tests for RunIDGenerator."""

import re
import pytest
from datetime import datetime
from pathlib import Path

from llm_sim.persistence.run_id_generator import RunIDGenerator
from llm_sim.persistence.exceptions import RunIDCollisionError


def test_generate_format():
    """Test generated ID matches expected format."""
    run_id = RunIDGenerator.generate(
        simulation_name="EconomicTest",
        num_agents=3,
        start_time=datetime(2025, 10, 1, 14, 30, 22),
        output_root=Path("/tmp/test_nonexistent")
    )

    pattern = r"^EconomicTest_3agents_20251001_143022_\d{2}$"
    assert re.match(pattern, run_id), f"Run ID '{run_id}' does not match expected pattern"


def test_generate_increments_sequence(tmp_path):
    """Test sequence increments when directory exists."""
    # Create existing directory
    (tmp_path / "Test_2agents_20251001_120000_01").mkdir(parents=True)

    run_id = RunIDGenerator.generate(
        "Test", 2, datetime(2025, 10, 1, 12, 0, 0), tmp_path
    )

    assert run_id == "Test_2agents_20251001_120000_02"


def test_generate_sanitizes_name():
    """Test sanitizes special characters in simulation name."""
    run_id = RunIDGenerator.generate(
        "Test/With Spaces",
        2,
        datetime(2025, 10, 1, 12, 0, 0),
        Path("/tmp/test_nonexistent")
    )

    assert "/" not in run_id
    # Spaces should be replaced with underscores
    assert "Test_With_Spaces" in run_id or "Test_With" in run_id


def test_generate_raises_on_too_many_collisions(tmp_path):
    """Test raises error if sequence exceeds 99."""
    # Create directories 01-99
    for seq in range(1, 100):
        (tmp_path / f"Test_2agents_20251001_120000_{seq:02d}").mkdir(parents=True)

    with pytest.raises(RunIDCollisionError):
        RunIDGenerator.generate("Test", 2, datetime(2025, 10, 1, 12, 0, 0), tmp_path)
