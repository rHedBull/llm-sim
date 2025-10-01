"""Integration test for full simulation with checkpoints."""

import pytest
from pathlib import Path
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    AgentConfig,
    ValidatorConfig,
)
from llm_sim.orchestrator import SimulationOrchestrator


def create_test_config(checkpoint_interval=None, max_turns=15):
    """Create a test simulation configuration."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="TestSim",
            max_turns=max_turns,
            checkpoint_interval=checkpoint_interval,
        ),
        engine=EngineConfig(type="economic", interest_rate=0.05),
        agents=[
            AgentConfig(name="Agent1", type="nation", initial_economic_strength=1000.0),
            AgentConfig(name="Agent2", type="nation", initial_economic_strength=1000.0),
        ],
        validator=ValidatorConfig(type="always_valid"),
    )


def test_full_simulation_with_checkpoints(tmp_path):
    """Test: Run 15-turn simulation with checkpoint_interval=5."""
    config = create_test_config(checkpoint_interval=5, max_turns=15)
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    result = orchestrator.run()

    # Verify result contains run_id
    assert "run_id" in result
    run_id = result["run_id"]

    # Verify checkpoint files exist
    run_dir = tmp_path / run_id
    assert (run_dir / "checkpoints" / "turn_5.json").exists()
    assert (run_dir / "checkpoints" / "turn_10.json").exists()
    assert (run_dir / "checkpoints" / "turn_15.json").exists()
    assert (run_dir / "checkpoints" / "last.json").exists()

    # Verify result.json exists
    assert (run_dir / "result.json").exists()


def test_checkpoint_interval_disabled(tmp_path):
    """Test: No interval checkpoints when disabled."""
    config = create_test_config(checkpoint_interval=None, max_turns=10)
    orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

    result = orchestrator.run()
    run_id = result["run_id"]

    # Verify only final checkpoint exists (no intervals)
    checkpoint_dir = tmp_path / run_id / "checkpoints"
    checkpoints = list(checkpoint_dir.glob("turn_*.json"))

    # Should only have final checkpoint (turn 10)
    assert len(checkpoints) == 1
    assert checkpoints[0].name == "turn_10.json"
