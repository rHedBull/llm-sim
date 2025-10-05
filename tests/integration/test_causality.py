"""Integration tests for event causality integrity.

Tests validate that causality references form valid graphs.
Based on quickstart.md Scenario 5: Causality integrity.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from ulid import ULID

from llm_sim.infrastructure.events import EventWriter, VerbosityLevel
from llm_sim.infrastructure.events.builder import (
    create_milestone_event,
    create_action_event,
    create_state_event,
)


@pytest_asyncio.fixture
async def event_dir_with_causality(tmp_path):
    """Create event directory with causality relationships."""
    output_dir = tmp_path / "output" / "causality-test"
    output_dir.mkdir(parents=True)

    event_writer = EventWriter(
        output_dir=output_dir,
        simulation_id="causality-test",
        verbosity=VerbosityLevel.STATE
    )

    await event_writer.start()

    # Create event chain with causality
    # Event 1: Turn start (no parent)
    turn_start = create_milestone_event(
        simulation_id="causality-test",
        turn_number=1,
        milestone_type="turn_start"
    )
    event_writer.emit(turn_start)

    # Event 2: Action caused by turn start
    action = create_action_event(
        simulation_id="causality-test",
        turn_number=1,
        agent_id="agent_alice",
        action_type="trade",
        action_payload={"amount": 100},
        caused_by=[turn_start.event_id]
    )
    event_writer.emit(action)

    # Event 3: State change caused by action
    state_change = create_state_event(
        simulation_id="causality-test",
        turn_number=1,
        variable_name="wealth",
        old_value=1000,
        new_value=1100,
        agent_id="agent_alice",
        caused_by=[action.event_id]
    )
    event_writer.emit(state_change)

    # Event 4: Turn end caused by state change
    turn_end = create_milestone_event(
        simulation_id="causality-test",
        turn_number=1,
        milestone_type="turn_end",
        caused_by=[state_change.event_id]
    )
    event_writer.emit(turn_end)

    # Allow events to be written
    await asyncio.sleep(0.1)
    await event_writer.stop(timeout=5.0)

    return output_dir


@pytest.mark.asyncio
async def test_causality_references_exist(event_dir_with_causality):
    """T023: Verify all caused_by event_ids exist."""
    events_file = event_dir_with_causality / "events.jsonl"

    # Load all events
    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Build set of all event IDs
    event_ids = {e["event_id"] for e in events}

    # Verify all causality references exist
    missing_refs = []
    for event in events:
        if "caused_by" in event and event["caused_by"]:
            for parent_id in event["caused_by"]:
                if parent_id not in event_ids:
                    missing_refs.append((event["event_id"], parent_id))

    assert len(missing_refs) == 0, \
        f"Found {len(missing_refs)} missing causality references: {missing_refs[:5]}"


@pytest.mark.asyncio
async def test_no_cyclic_causality(event_dir_with_causality):
    """Verify causality graph has no cycles."""
    events_file = event_dir_with_causality / "events.jsonl"

    # Load all events
    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Build causality graph
    graph = {}
    for event in events:
        event_id = event["event_id"]
        caused_by = event.get("caused_by", []) or []
        graph[event_id] = caused_by

    # Detect cycles using DFS
    def has_cycle(event_id, visited=None, rec_stack=None):
        if visited is None:
            visited = set()
        if rec_stack is None:
            rec_stack = set()

        visited.add(event_id)
        rec_stack.add(event_id)

        # Visit all parents
        for parent_id in graph.get(event_id, []):
            if parent_id not in visited:
                if has_cycle(parent_id, visited, rec_stack):
                    return True
            elif parent_id in rec_stack:
                return True

        rec_stack.remove(event_id)
        return False

    # Check for cycles
    cycles = []
    for event_id in graph:
        if has_cycle(event_id):
            cycles.append(event_id)

    assert len(cycles) == 0, \
        f"Found {len(cycles)} events with cyclic causality: {cycles[:5]}"


@pytest.mark.asyncio
async def test_causality_temporal_consistency(event_dir_with_causality):
    """Verify child events occur after parent events."""
    events_file = event_dir_with_causality / "events.jsonl"

    # Load all events
    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Build event lookup by ID
    event_by_id = {e["event_id"]: e for e in events}

    # Verify temporal ordering
    violations = []
    for event in events:
        if "caused_by" in event and event["caused_by"]:
            child_timestamp = datetime.fromisoformat(event["timestamp"])

            for parent_id in event["caused_by"]:
                parent = event_by_id.get(parent_id)
                if parent:
                    parent_timestamp = datetime.fromisoformat(parent["timestamp"])

                    # Parent should occur before or at same time as child
                    if parent_timestamp > child_timestamp:
                        violations.append({
                            "child": event["event_id"],
                            "parent": parent_id,
                            "child_time": child_timestamp,
                            "parent_time": parent_timestamp
                        })

    assert len(violations) == 0, \
        f"Found {len(violations)} temporal causality violations: {violations[:3]}"


@pytest.mark.asyncio
async def test_causality_chain_depth(event_dir_with_causality):
    """Verify causality chains can be traversed to full depth."""
    events_file = event_dir_with_causality / "events.jsonl"

    # Load all events
    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Build causality graph
    graph = {e["event_id"]: e.get("caused_by", []) or [] for e in events}

    # Find max chain depth
    def get_depth(event_id, visited=None):
        if visited is None:
            visited = set()

        if event_id in visited:
            return 0  # Prevent infinite recursion

        visited.add(event_id)
        parents = graph.get(event_id, [])

        if not parents:
            return 0

        return 1 + max(get_depth(p, visited.copy()) for p in parents)

    # Calculate depth for all events
    depths = {e["event_id"]: get_depth(e["event_id"]) for e in events}
    max_depth = max(depths.values()) if depths else 0

    # Verify we have some causality depth
    assert max_depth > 0, "No causality chains found"
    assert max_depth >= 3, \
        f"Expected causality depth >= 3 (turn_start -> action -> state -> turn_end), got {max_depth}"


@pytest.mark.asyncio
async def test_multi_parent_causality(tmp_path):
    """Verify events can have multiple causal parents."""
    output_dir = tmp_path / "output" / "multi-parent-test"
    output_dir.mkdir(parents=True)

    event_writer = EventWriter(
        output_dir=output_dir,
        simulation_id="multi-parent-test",
        verbosity=VerbosityLevel.STATE
    )

    await event_writer.start()

    # Create two parent events
    action1 = create_action_event(
        simulation_id="multi-parent-test",
        turn_number=1,
        agent_id="agent_alice",
        action_type="offer",
        action_payload={"amount": 50}
    )
    event_writer.emit(action1)

    action2 = create_action_event(
        simulation_id="multi-parent-test",
        turn_number=1,
        agent_id="agent_bob",
        action_type="accept",
        action_payload={"amount": 50}
    )
    event_writer.emit(action2)

    # Create child event with two parents
    state_change = create_state_event(
        simulation_id="multi-parent-test",
        turn_number=1,
        variable_name="trade_completed",
        old_value=False,
        new_value=True,
        caused_by=[action1.event_id, action2.event_id]  # Two parents
    )
    event_writer.emit(state_change)

    # Allow events to be written
    await asyncio.sleep(0.1)
    await event_writer.stop(timeout=5.0)

    # Verify multi-parent causality
    events_file = output_dir / "events.jsonl"
    events = []
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))

    # Find the state change event
    state_event = next(e for e in events if e.get("details", {}).get("variable_name") == "trade_completed")
    assert len(state_event["caused_by"]) == 2, \
        f"Expected 2 parents, got {len(state_event['caused_by'])}"

    # Verify both parents exist
    parent_ids = set(state_event["caused_by"])
    assert action1.event_id in parent_ids
    assert action2.event_id in parent_ids
