"""Integration tests for orchestrator event emission.

Tests validate that the orchestrator correctly emits events during simulation execution.
Based on quickstart.md Scenario 1: Basic event capture.
"""

import json
from pathlib import Path
from datetime import datetime

import pytest

from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    AgentConfig,
    EngineConfig,
    ValidatorConfig,
)
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.infrastructure.events import VerbosityLevel, EventWriter


@pytest.fixture
def minimal_config():
    """Create minimal simulation config for testing."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="event-stream-test",
            max_turns=3,
            checkpoint_interval=999  # Disable checkpoints
        ),
        agents=[
            AgentConfig(
                name="agent_alpha",
                type="simple",
                initial_state={"wealth": 1000}
            )
        ],
        global_state={"turn": 0},
        engine=EngineConfig(type="simple_economic"),
        validator=ValidatorConfig(type="basic")
    )


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_basic_event_capture(minimal_config, tmp_output_dir):
    """T016: Verify simulation emits events to JSONL file."""
    # Create orchestrator with event streaming
    orchestrator = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir,
        event_verbosity=VerbosityLevel.ACTION
    )

    # Run simulation
    result = orchestrator.run()

    # Verify events file was created
    run_id = orchestrator.run_id
    events_file = tmp_output_dir / run_id / "events.jsonl"
    assert events_file.exists(), f"Events file not found at {events_file}"
    assert events_file.stat().st_size > 0, "Events file is empty"

    # Verify file contains valid JSONL
    events = []
    with open(events_file, "r") as f:
        for i, line in enumerate(f):
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i} is not valid JSON: {line[:100]}... Error: {e}")

    # Verify basic event structure
    assert len(events) > 0, "No events were emitted"

    for event in events:
        assert "event_id" in event, f"Event missing event_id: {event}"
        assert "timestamp" in event, f"Event missing timestamp: {event}"
        assert "turn_number" in event, f"Event missing turn_number: {event}"
        assert "event_type" in event, f"Event missing event_type: {event}"
        assert "simulation_id" in event, f"Event missing simulation_id: {event}"

    # Verify MILESTONE events are present
    milestone_events = [e for e in events if e["event_type"] == "MILESTONE"]
    assert len(milestone_events) > 0, "No MILESTONE events found"

    # Verify simulation_start and simulation_end events
    milestone_types = [e["details"]["milestone_type"] for e in milestone_events]
    assert "simulation_start" in milestone_types, "No simulation_start milestone"
    assert "simulation_end" in milestone_types, "No simulation_end milestone"

    # Verify turn_start and turn_end events for each turn
    turn_start_count = sum(1 for mt in milestone_types if mt == "turn_start")
    turn_end_count = sum(1 for mt in milestone_types if mt == "turn_end")

    # Should have turn_start and turn_end for each turn (3 turns)
    assert turn_start_count == 3, f"Expected 3 turn_start events, got {turn_start_count}"
    assert turn_end_count == 3, f"Expected 3 turn_end events, got {turn_end_count}"


def test_event_chronological_order(minimal_config, tmp_output_dir):
    """Verify events are in chronological order."""
    orchestrator = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir,
        event_verbosity=VerbosityLevel.ACTION
    )

    result = orchestrator.run()

    # Load events
    run_id = orchestrator.run_id
    events_file = tmp_output_dir / run_id / "events.jsonl"

    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Verify timestamps are in chronological order
    timestamps = [datetime.fromisoformat(e["timestamp"]) for e in events]
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i-1], \
            f"Event {i} timestamp {timestamps[i]} is before event {i-1} timestamp {timestamps[i-1]}"

    # Verify turn numbers are non-decreasing
    turn_numbers = [e["turn_number"] for e in events]
    for i in range(1, len(turn_numbers)):
        assert turn_numbers[i] >= turn_numbers[i-1], \
            f"Event {i} turn {turn_numbers[i]} is before event {i-1} turn {turn_numbers[i-1]}"


def test_simulation_id_consistency(minimal_config, tmp_output_dir):
    """Verify all events have the same simulation_id."""
    orchestrator = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir,
        event_verbosity=VerbosityLevel.ACTION
    )

    result = orchestrator.run()

    # Load events
    run_id = orchestrator.run_id
    events_file = tmp_output_dir / run_id / "events.jsonl"

    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Verify all events have same simulation_id
    simulation_ids = set(e["simulation_id"] for e in events)
    assert len(simulation_ids) == 1, f"Multiple simulation_ids found: {simulation_ids}"
    assert list(simulation_ids)[0] == run_id, f"simulation_id {list(simulation_ids)[0]} doesn't match run_id {run_id}"


def test_ulid_uniqueness(minimal_config, tmp_output_dir):
    """Verify all event_ids are unique ULIDs."""
    orchestrator = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir,
        event_verbosity=VerbosityLevel.ACTION
    )

    result = orchestrator.run()

    # Load events
    run_id = orchestrator.run_id
    events_file = tmp_output_dir / run_id / "events.jsonl"

    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Verify all event_ids are unique
    event_ids = [e["event_id"] for e in events]
    assert len(event_ids) == len(set(event_ids)), "Duplicate event_ids found"

    # Verify all event_ids are valid ULIDs (26 characters, Base32)
    for event_id in event_ids:
        assert len(event_id) == 26, f"Invalid ULID length: {event_id}"
        assert event_id.replace('-', '').replace('_', '').isalnum(), f"Invalid ULID characters: {event_id}"
