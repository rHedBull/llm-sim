"""Integration test for run ID uniqueness."""

import re
import pytest
from datetime import datetime
from unittest.mock import patch

from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    AgentConfig,
    ValidatorConfig,
)
from llm_sim.orchestrator import SimulationOrchestrator


def create_test_config():
    """Create a test simulation configuration."""
    return SimulationConfig(
        simulation=SimulationSettings(name="TestSim", max_turns=5),
        engine=EngineConfig(type="economic", interest_rate=0.05),
        agents=[
            AgentConfig(name="Agent1", type="nation", initial_economic_strength=1000.0),
        ],
        validator=ValidatorConfig(type="always_valid"),
    )


def test_concurrent_runs_unique_ids(tmp_path):
    """Test: Create two simulations with same config in same second."""
    config = create_test_config()

    # Simulate concurrent starts (same timestamp)
    with patch("llm_sim.orchestrator.datetime") as mock_dt:
        fixed_time = datetime(2025, 10, 1, 12, 0, 0)
        mock_dt.now.return_value = fixed_time

        orch1 = SimulationOrchestrator(config, output_root=tmp_path)
        run_id_1 = orch1.run_id

        orch2 = SimulationOrchestrator(config, output_root=tmp_path)
        run_id_2 = orch2.run_id

    # Verify unique IDs (sequence incremented)
    assert run_id_1.endswith("_01")
    assert run_id_2.endswith("_02")
    assert run_id_1 != run_id_2


def test_run_id_format(tmp_path):
    """Test: Verify run ID format matches specification."""
    config = create_test_config()
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    run_id = orchestrator.run_id

    # Format: {name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}
    pattern = r"^TestSim_1agents_\d{8}_\d{6}_\d{2}$"
    assert re.match(pattern, run_id), f"Run ID '{run_id}' does not match expected pattern"
