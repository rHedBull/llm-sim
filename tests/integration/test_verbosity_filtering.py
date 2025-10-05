"""Integration tests for verbosity level filtering.

Tests validate that different verbosity levels capture correct event types.
Based on quickstart.md Scenario 2: MILESTONE verbosity filtering.
"""

import json
from pathlib import Path

import pytest

from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    AgentConfig,
    EngineConfig,
    ValidatorConfig,
)
from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.infrastructure.events import VerbosityLevel


@pytest.fixture
def minimal_config():
    """Create minimal simulation config for testing."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="verbosity-test",
            max_turns=3,
            checkpoint_interval=999
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


def test_milestone_verbosity_only_milestones(minimal_config, tmp_output_dir):
    """T017: Verify MILESTONE verbosity captures only MILESTONE events."""
    orchestrator = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir,
        event_verbosity=VerbosityLevel.MILESTONE
    )

    result = orchestrator.run()

    # Load events
    run_id = orchestrator.run_id
    events_file = tmp_output_dir / run_id / "events.jsonl"

    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Verify only MILESTONE events
    event_types = set(e["event_type"] for e in events)
    assert event_types == {"MILESTONE"}, \
        f"MILESTONE verbosity should only have MILESTONE events, found: {event_types}"

    # Verify minimum number of milestones (start + end + turns)
    assert len(events) >= 8, \
        f"Expected at least 8 MILESTONE events (start + 3×(turn_start+turn_end) + end), got {len(events)}"


def test_detail_verbosity_captures_more_events(minimal_config, tmp_output_dir):
    """T018: Verify DETAIL verbosity captures more events than MILESTONE."""
    # Run with MILESTONE verbosity
    orchestrator_milestone = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir / "milestone",
        event_verbosity=VerbosityLevel.MILESTONE
    )
    result_milestone = orchestrator_milestone.run()

    # Load milestone events
    run_id_milestone = orchestrator_milestone.run_id
    events_file_milestone = tmp_output_dir / "milestone" / run_id_milestone / "events.jsonl"

    milestone_events = []
    with open(events_file_milestone, "r") as f:
        for line in f:
            milestone_events.append(json.loads(line))

    # Run with DETAIL verbosity
    orchestrator_detail = SimulationOrchestrator(
        config=minimal_config,
        output_root=tmp_output_dir / "detail",
        event_verbosity=VerbosityLevel.DETAIL
    )
    result_detail = orchestrator_detail.run()

    # Load detail events
    run_id_detail = orchestrator_detail.run_id
    events_file_detail = tmp_output_dir / "detail" / run_id_detail / "events.jsonl"

    detail_events = []
    with open(events_file_detail, "r") as f:
        for line in f:
            detail_events.append(json.loads(line))

    # Verify DETAIL has more events than MILESTONE
    assert len(detail_events) > len(milestone_events), \
        f"DETAIL verbosity ({len(detail_events)} events) should capture more than MILESTONE ({len(milestone_events)} events)"


def test_verbosity_hierarchy(minimal_config, tmp_output_dir):
    """Verify verbosity levels follow hierarchical inclusion."""
    # MILESTONE < DECISION < ACTION < STATE < DETAIL
    # Each level should include events from lower levels

    results = {}

    for verbosity in [VerbosityLevel.MILESTONE, VerbosityLevel.ACTION, VerbosityLevel.DETAIL]:
        orchestrator = SimulationOrchestrator(
            config=minimal_config,
            output_root=tmp_output_dir / verbosity.value,
            event_verbosity=verbosity
        )
        result = orchestrator.run()

        run_id = orchestrator.run_id
        events_file = tmp_output_dir / verbosity.value / run_id / "events.jsonl"

        events = []
        with open(events_file, "r") as f:
            for line in f:
                events.append(json.loads(line))

        results[verbosity] = events

    # Verify hierarchy: MILESTONE ⊆ ACTION ⊆ DETAIL
    milestone_count = len(results[VerbosityLevel.MILESTONE])
    action_count = len(results[VerbosityLevel.ACTION])
    detail_count = len(results[VerbosityLevel.DETAIL])

    assert milestone_count <= action_count, \
        f"MILESTONE ({milestone_count}) should have fewer or equal events than ACTION ({action_count})"
    assert action_count <= detail_count, \
        f"ACTION ({action_count}) should have fewer or equal events than DETAIL ({detail_count})"

    # Verify MILESTONE events are present in all levels
    milestone_event_ids = {e["event_id"] for e in results[VerbosityLevel.MILESTONE]}
    action_event_ids = {e["event_id"] for e in results[VerbosityLevel.ACTION]}
    detail_event_ids = {e["event_id"] for e in results[VerbosityLevel.DETAIL]}

    # Note: Event IDs will be different across runs, so we check event types instead
    milestone_types_in_action = {e["event_type"] for e in results[VerbosityLevel.ACTION]}
    milestone_types_in_detail = {e["event_type"] for e in results[VerbosityLevel.DETAIL]}

    assert "MILESTONE" in milestone_types_in_action, "ACTION level should include MILESTONE events"
    assert "MILESTONE" in milestone_types_in_detail, "DETAIL level should include MILESTONE events"


def test_action_verbosity_excludes_state_detail(minimal_config, tmp_output_dir):
    """Verify ACTION verbosity excludes STATE and DETAIL events."""
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

    # Verify no STATE or DETAIL events
    event_types = {e["event_type"] for e in events}
    assert "STATE" not in event_types, "ACTION verbosity should not include STATE events"
    assert "DETAIL" not in event_types, "ACTION verbosity should not include DETAIL events"

    # Should include MILESTONE, potentially DECISION and ACTION
    assert "MILESTONE" in event_types, "ACTION verbosity should include MILESTONE events"
