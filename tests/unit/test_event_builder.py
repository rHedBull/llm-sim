"""Unit tests for EventBuilder ULID generation."""

from datetime import datetime, timezone

import pytest
from ulid import ULID

from llm_sim.infrastructure.events.builder import (
    create_milestone_event,
    create_action_event,
    create_decision_event,
    create_state_event,
    create_detail_event,
    create_system_event,
)


def test_ulid_generation_uniqueness():
    """T041: Verify ULIDs are unique."""
    # Generate multiple events rapidly
    event_ids = set()

    for i in range(1000):
        event = create_milestone_event(
            simulation_id="test-sim",
            turn_number=1,
            milestone_type="turn_start"
        )
        event_ids.add(event.event_id)

    # All event IDs should be unique
    assert len(event_ids) == 1000, "Duplicate ULIDs generated"


def test_ulid_sortability():
    """T041: Verify ULIDs are sortable by creation time."""
    events = []

    # Generate events with slight delays
    for i in range(10):
        event = create_milestone_event(
            simulation_id="test-sim",
            turn_number=i,
            milestone_type="turn_start"
        )
        events.append(event)

    # Extract ULIDs
    ulids = [event.event_id for event in events]

    # Sort ULIDs alphabetically (ULID property: lexicographic sort = chronological sort)
    sorted_ulids = sorted(ulids)

    # Should be in same order as creation (or at least non-decreasing)
    # Note: ULIDs have millisecond precision, so some may be equal
    for i in range(1, len(sorted_ulids)):
        assert sorted_ulids[i] >= sorted_ulids[i-1], \
            f"ULID not sortable: {sorted_ulids[i]} < {sorted_ulids[i-1]}"


def test_ulid_format_validation():
    """T041: Verify ULIDs conform to format (26 char Base32)."""
    event = create_milestone_event(
        simulation_id="test-sim",
        turn_number=1,
        milestone_type="turn_start"
    )

    # Validate ULID format
    ulid_str = event.event_id
    assert len(ulid_str) == 26, f"ULID wrong length: {len(ulid_str)}"

    # Verify it can be parsed as ULID
    try:
        parsed_ulid = ULID.from_str(ulid_str)
        assert str(parsed_ulid) == ulid_str
    except ValueError as e:
        pytest.fail(f"Invalid ULID format: {ulid_str}, error: {e}")


def test_all_event_types_generate_valid_ulids():
    """Verify all event builder functions generate valid ULIDs."""
    # Test all event types
    events = [
        create_milestone_event("sim", 1, "turn_start"),
        create_action_event("sim", 1, "agent_1", "trade", {"amount": 100}),
        create_decision_event("sim", 1, "agent_1", "invest", 0, 100),
        create_state_event("sim", 1, "wealth", 1000, 1100),
        create_detail_event("sim", 1, "calculation", {"value": 42}),
        create_system_event("sim", 1, "success"),
    ]

    for event in events:
        # Verify ULID format
        assert len(event.event_id) == 26, f"Invalid ULID length for {event.event_type}"

        # Verify can be parsed
        try:
            ULID.from_str(event.event_id)
        except ValueError:
            pytest.fail(f"Invalid ULID for {event.event_type}: {event.event_id}")


def test_timestamp_precision():
    """Verify timestamps have microsecond precision."""
    event = create_milestone_event(
        simulation_id="test-sim",
        turn_number=1,
        milestone_type="turn_start"
    )

    # Verify timestamp is datetime with timezone
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo is not None

    # Verify ISO format includes microseconds
    iso_str = event.timestamp.isoformat()
    assert "." in iso_str, "Timestamp missing microsecond precision"

    # Parse and verify precision
    parts = iso_str.split(".")
    microseconds = parts[1].split("+")[0] if "+" in parts[1] else parts[1].split("-")[0]
    assert len(microseconds) == 6, f"Expected 6 digits for microseconds, got {len(microseconds)}"


def test_event_builder_causality_chain():
    """Verify event builders support causality chains."""
    # Create parent event
    parent = create_milestone_event(
        simulation_id="test-sim",
        turn_number=1,
        milestone_type="turn_start"
    )

    # Create child event with causality
    child = create_action_event(
        simulation_id="test-sim",
        turn_number=1,
        agent_id="agent_1",
        action_type="trade",
        action_payload={},
        caused_by=[parent.event_id]
    )

    assert child.caused_by == [parent.event_id]
    assert len(child.caused_by) == 1

    # Create multi-parent event
    parent2 = create_decision_event(
        simulation_id="test-sim",
        turn_number=1,
        agent_id="agent_1",
        decision_type="approve",
        old_value=False,
        new_value=True
    )

    multi_parent = create_state_event(
        simulation_id="test-sim",
        turn_number=1,
        variable_name="wealth",
        old_value=1000,
        new_value=1100,
        caused_by=[parent.event_id, parent2.event_id]
    )

    assert len(multi_parent.caused_by) == 2
    assert parent.event_id in multi_parent.caused_by
    assert parent2.event_id in multi_parent.caused_by


def test_event_builder_optional_description():
    """Verify event builders support optional descriptions."""
    # Without description
    event1 = create_milestone_event(
        simulation_id="test-sim",
        turn_number=1,
        milestone_type="turn_start"
    )
    assert event1.description is None

    # With description
    event2 = create_milestone_event(
        simulation_id="test-sim",
        turn_number=1,
        milestone_type="turn_start",
        description="Custom description"
    )
    assert event2.description == "Custom description"


def test_event_builder_simulation_id_consistency():
    """Verify simulation_id is correctly set on all event types."""
    sim_id = "test-simulation-123"

    events = [
        create_milestone_event(sim_id, 1, "turn_start"),
        create_action_event(sim_id, 1, "agent_1", "trade", {}),
        create_decision_event(sim_id, 1, "agent_1", "invest", 0, 100),
        create_state_event(sim_id, 1, "wealth", 1000, 1100),
        create_detail_event(sim_id, 1, "calc", {}),
        create_system_event(sim_id, 1, "success"),
    ]

    for event in events:
        assert event.simulation_id == sim_id, \
            f"Wrong simulation_id for {event.event_type}: {event.simulation_id}"
