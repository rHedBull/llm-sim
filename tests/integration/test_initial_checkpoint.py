"""Integration test for initial checkpoint creation at turn 0."""

import json
import pytest
from pathlib import Path

from llm_sim.orchestrator import Orchestrator
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    AgentConfig,
    EngineConfig,
    ValidatorConfig,
)


def test_initial_checkpoint_created_sync(tmp_path):
    """Test that initial checkpoint at turn 0 is always created (sync mode)."""
    # Create minimal config
    config = SimulationConfig(
        simulation=SimulationSettings(
            name="initial-checkpoint-test",
            max_turns=3,
            checkpoint_interval=999  # High interval so only initial/final checkpoints created
        ),
        agents=[
            AgentConfig(
                name="test_agent",
                type="simple",
                initial_state={"wealth": 1000}
            )
        ],
        global_state={"turn": 0},
        engine=EngineConfig(type="simple_economic"),
        validator=ValidatorConfig(type="basic")
    )

    # Run simulation
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    orchestrator = Orchestrator(config, output_root=output_dir)
    orchestrator.run()

    # Check initial checkpoint exists
    checkpoint_dir = output_dir / orchestrator.run_id / "checkpoints"
    initial_checkpoint = checkpoint_dir / "turn_0.json"

    assert initial_checkpoint.exists(), "Initial checkpoint at turn 0 not created"

    # Verify it's valid and contains turn 0
    with open(initial_checkpoint) as f:
        checkpoint_data = json.load(f)
    assert checkpoint_data["state"]["turn"] == 0, "Initial checkpoint should be at turn 0"
    assert checkpoint_data["metadata"]["turn"] == 0, "Metadata should indicate turn 0"


def test_initial_checkpoint_contains_initial_state(tmp_path):
    """Test that initial checkpoint preserves the exact initial state."""
    # Create config with specific initial values
    config = SimulationConfig(
        simulation=SimulationSettings(
            name="initial-state-test",
            max_turns=2,
            checkpoint_interval=999
        ),
        agents=[
            AgentConfig(
                name="agent_1",
                type="simple",
                initial_state={"wealth": 5000, "happiness": 100}
            ),
            AgentConfig(
                name="agent_2",
                type="simple",
                initial_state={"wealth": 3000, "happiness": 80}
            )
        ],
        global_state={"total_wealth": 8000},
        engine=EngineConfig(type="simple_economic"),
        validator=ValidatorConfig(type="basic")
    )

    # Run simulation
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    orchestrator = Orchestrator(config, output_root=output_dir)
    orchestrator.run()

    # Load initial checkpoint
    checkpoint_dir = output_dir / orchestrator.run_id / "checkpoints"
    initial_checkpoint = checkpoint_dir / "turn_0.json"
    with open(initial_checkpoint) as f:
        checkpoint_data = json.load(f)

    # Verify checkpoint structure and turn number
    state = checkpoint_data["state"]
    assert state["turn"] == 0, "Initial checkpoint should be at turn 0"

    # Verify metadata
    assert checkpoint_data["metadata"]["turn"] == 0

    # Verify basic structure is present
    assert "agents" in state
    assert "global_state" in state


def test_initial_checkpoint_always_created_regardless_of_interval(tmp_path):
    """Test that initial checkpoint is created even when checkpoint_interval is None."""
    config = SimulationConfig(
        simulation=SimulationSettings(
            name="no-interval-test",
            max_turns=5,
            checkpoint_interval=None  # No interval checkpoints
        ),
        agents=[
            AgentConfig(
                name="test_agent",
                type="simple",
                initial_state={"wealth": 1000}
            )
        ],
        global_state={"turn": 0},
        engine=EngineConfig(type="simple_economic"),
        validator=ValidatorConfig(type="basic")
    )

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    orchestrator = Orchestrator(config, output_root=output_dir)
    orchestrator.run()

    # Check initial checkpoint exists even with no interval
    checkpoint_dir = output_dir / orchestrator.run_id / "checkpoints"
    initial_checkpoint = checkpoint_dir / "turn_0.json"

    assert initial_checkpoint.exists(), "Initial checkpoint should always be created"

    # Verify that intermediate checkpoints weren't created (only turn_0 and turn_5 final)
    checkpoint_files = sorted(checkpoint_dir.glob("turn_*.json"))
    turn_numbers = [int(f.stem.split("_")[1]) for f in checkpoint_files]

    # Should have turn_0 (initial) and turn_5 (final)
    assert 0 in turn_numbers, "Turn 0 checkpoint missing"
    assert 5 in turn_numbers, "Final checkpoint missing"
    # No intermediate turns
    assert all(t in [0, 5] for t in turn_numbers), f"Unexpected checkpoints: {turn_numbers}"
