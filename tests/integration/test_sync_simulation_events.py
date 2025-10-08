"""Integration test for sync EventWriter with simulation."""

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


def test_sync_simulation_creates_events(tmp_path):
    """Test that sync simulation mode creates events.jsonl.

    This is the end-to-end test validating the fix for missing events.jsonl files.
    """
    # Create minimal config
    config = SimulationConfig(
        simulation=SimulationSettings(
            name="sync-event-test",
            max_turns=2,
            checkpoint_interval=999
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

    # Run simulation with tmp output dir
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    orchestrator = Orchestrator(config, output_root=output_dir)
    orchestrator.run()  # Sync call - orchestrator handles async internally

    # Check events file exists
    event_files = list(output_dir.glob("*/events.jsonl"))
    assert len(event_files) > 0, "No events.jsonl created - bug not fixed!"

    # Check events were written
    event_content = event_files[0].read_text()
    event_lines = event_content.strip().split("\n")
    assert len(event_lines) > 0, "events.jsonl is empty"

    # Check for expected event types (looking for actual emitted events)
    assert any("simulation_starting" in line or "turn_" in line for line in event_lines), \
        "Expected simulation events not found"
