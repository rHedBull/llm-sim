"""Unit tests for EventFilter application logic."""

from datetime import datetime, timezone, timedelta

import pytest

from llm_sim.models.event_filter import EventFilter
from llm_sim.infrastructure.events.builder import (
    create_milestone_event,
    create_action_event,
    create_decision_event,
)


@pytest.fixture
def sample_events():
    """Create sample events for filtering tests."""
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    events = [
        create_milestone_event(
            simulation_id="test-sim",
            turn_number=1,
            milestone_type="turn_start"
        ),
        create_action_event(
            simulation_id="test-sim",
            turn_number=1,
            agent_id="agent_alice",
            action_type="trade",
            action_payload={"amount": 100}
        ),
        create_decision_event(
            simulation_id="test-sim",
            turn_number=1,
            agent_id="agent_bob",
            decision_type="invest",
            old_value=0,
            new_value=50
        ),
        create_milestone_event(
            simulation_id="test-sim",
            turn_number=1,
            milestone_type="turn_end"
        ),
        create_action_event(
            simulation_id="test-sim",
            turn_number=2,
            agent_id="agent_alice",
            action_type="sell",
            action_payload={"amount": 50}
        ),
        create_milestone_event(
            simulation_id="test-sim",
            turn_number=2,
            milestone_type="turn_end"
        ),
    ]

    # Update timestamps to be sequential
    for i, event in enumerate(events):
        event.timestamp = base_time + timedelta(seconds=i)

    return events


def test_filter_by_event_types(sample_events):
    """T042: Test filtering by event_types."""
    event_filter = EventFilter(event_types=["MILESTONE"])

    filtered = [e for e in sample_events if e.event_type in event_filter.event_types]

    assert len(filtered) == 3, f"Expected 3 MILESTONE events, got {len(filtered)}"
    assert all(e.event_type == "MILESTONE" for e in filtered)


def test_filter_by_agent_ids(sample_events):
    """T042: Test filtering by agent_ids."""
    event_filter = EventFilter(agent_ids=["agent_alice"])

    filtered = [
        e for e in sample_events
        if e.agent_id and e.agent_id in event_filter.agent_ids
    ]

    assert len(filtered) == 2, f"Expected 2 events from agent_alice, got {len(filtered)}"
    assert all(e.agent_id == "agent_alice" for e in filtered)


def test_filter_by_turn_range(sample_events):
    """T042: Test filtering by turn_start and turn_end."""
    event_filter = EventFilter(turn_start=2, turn_end=2)

    filtered = [
        e for e in sample_events
        if event_filter.turn_start <= e.turn_number <= event_filter.turn_end
    ]

    assert len(filtered) == 2, f"Expected 2 events from turn 2, got {len(filtered)}"
    assert all(e.turn_number == 2 for e in filtered)


def test_filter_by_timestamp_range(sample_events):
    """T042: Test filtering by timestamp range."""
    # Get timestamp range from events
    start_time = sample_events[2].timestamp  # 3rd event
    end_time = sample_events[4].timestamp    # 5th event

    event_filter = EventFilter(
        start_timestamp=start_time,
        end_timestamp=end_time
    )

    filtered = [
        e for e in sample_events
        if event_filter.start_timestamp <= e.timestamp <= event_filter.end_timestamp
    ]

    # Should include events 2, 3, 4 (indices)
    assert len(filtered) == 3, f"Expected 3 events in timestamp range, got {len(filtered)}"


def test_filter_limit_and_offset(sample_events):
    """T042: Test pagination with limit and offset."""
    # First page
    event_filter1 = EventFilter(limit=2, offset=0)
    page1 = sample_events[event_filter1.offset:event_filter1.offset + event_filter1.limit]
    assert len(page1) == 2

    # Second page
    event_filter2 = EventFilter(limit=2, offset=2)
    page2 = sample_events[event_filter2.offset:event_filter2.offset + event_filter2.limit]
    assert len(page2) == 2

    # Pages should be different
    assert page1[0].event_id != page2[0].event_id


def test_filter_combined_criteria(sample_events):
    """Test filtering with multiple criteria combined."""
    event_filter = EventFilter(
        event_types=["ACTION"],
        agent_ids=["agent_alice"],
        turn_start=1,
        turn_end=2
    )

    # Apply all filters
    filtered = sample_events
    if event_filter.event_types:
        filtered = [e for e in filtered if e.event_type in event_filter.event_types]
    if event_filter.agent_ids:
        filtered = [e for e in filtered if e.agent_id and e.agent_id in event_filter.agent_ids]
    if event_filter.turn_start is not None and event_filter.turn_end is not None:
        filtered = [
            e for e in filtered
            if event_filter.turn_start <= e.turn_number <= event_filter.turn_end
        ]

    # Should match: ACTION events by agent_alice in turns 1-2
    assert len(filtered) == 2
    assert all(e.event_type == "ACTION" for e in filtered)
    assert all(e.agent_id == "agent_alice" for e in filtered)


def test_filter_default_values():
    """Verify EventFilter default values."""
    event_filter = EventFilter()

    assert event_filter.start_timestamp is None
    assert event_filter.end_timestamp is None
    assert event_filter.event_types is None
    assert event_filter.agent_ids is None
    assert event_filter.turn_start is None
    assert event_filter.turn_end is None
    assert event_filter.limit == 1000  # Default limit
    assert event_filter.offset == 0     # Default offset


def test_filter_empty_results():
    """Test filter with criteria that match no events."""
    event_filter = EventFilter(agent_ids=["nonexistent_agent"])

    sample_events_fixture = [
        create_action_event("sim", 1, "agent_alice", "trade", {})
    ]

    filtered = [
        e for e in sample_events_fixture
        if e.agent_id and e.agent_id in event_filter.agent_ids
    ]

    assert len(filtered) == 0


def test_filter_turn_range_validation():
    """Test turn range edge cases."""
    # turn_start only
    event_filter1 = EventFilter(turn_start=5)
    assert event_filter1.turn_start == 5
    assert event_filter1.turn_end is None

    # turn_end only
    event_filter2 = EventFilter(turn_end=10)
    assert event_filter2.turn_start is None
    assert event_filter2.turn_end == 10

    # Both specified
    event_filter3 = EventFilter(turn_start=5, turn_end=10)
    assert event_filter3.turn_start == 5
    assert event_filter3.turn_end == 10


def test_filter_multiple_event_types(sample_events):
    """Test filtering with multiple event types."""
    event_filter = EventFilter(event_types=["MILESTONE", "ACTION"])

    filtered = [e for e in sample_events if e.event_type in event_filter.event_types]

    # Should include all MILESTONE and ACTION events
    milestone_count = sum(1 for e in filtered if e.event_type == "MILESTONE")
    action_count = sum(1 for e in filtered if e.event_type == "ACTION")

    assert milestone_count == 3
    assert action_count == 2
    assert len(filtered) == 5


def test_filter_multiple_agent_ids(sample_events):
    """Test filtering with multiple agent IDs."""
    event_filter = EventFilter(agent_ids=["agent_alice", "agent_bob"])

    filtered = [
        e for e in sample_events
        if e.agent_id and e.agent_id in event_filter.agent_ids
    ]

    # Should include events from both agents
    assert len(filtered) == 3
    agent_ids = {e.agent_id for e in filtered}
    assert "agent_alice" in agent_ids
    assert "agent_bob" in agent_ids
