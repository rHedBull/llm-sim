"""Contract tests for Event schema validation.

Tests validate that all Event subclass schemas match the JSON schema contract
defined in specs/010-event-stream-the/contracts/event-schema.json.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ulid import ULID

from llm_sim.models.event import (
    Event,
    MilestoneEvent,
    DecisionEvent,
    ActionEvent,
    StateEvent,
    DetailEvent,
    SystemEvent,
)


def test_base_event_schema():
    """T005: Validate Event base model schema."""
    # Test required fields
    event = Event(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        event_type="MILESTONE",
        simulation_id="test-sim-123",
    )

    # Validate required fields present
    assert event.event_id is not None
    assert len(event.event_id) == 26  # ULID length
    assert event.timestamp is not None
    assert event.turn_number >= 0
    assert event.event_type in ["MILESTONE", "DECISION", "ACTION", "STATE", "DETAIL", "SYSTEM"]
    assert event.simulation_id == "test-sim-123"

    # Test optional fields
    event_with_optionals = Event(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        event_type="DECISION",
        simulation_id="test-sim-123",
        agent_id="agent_alice",
        caused_by=[str(ULID())],
        description="Test event",
        details={"key": "value"}
    )

    assert event_with_optionals.agent_id == "agent_alice"
    assert len(event_with_optionals.caused_by) == 1
    assert event_with_optionals.description == "Test event"
    assert event_with_optionals.details == {"key": "value"}


def test_milestone_event_schema():
    """T006: Validate MilestoneEvent subclass schema."""
    # Test valid milestone types
    milestone_types = ["turn_start", "turn_end", "phase_transition", "simulation_start", "simulation_end"]

    for milestone_type in milestone_types:
        event = MilestoneEvent(
            event_id=str(ULID()),
            timestamp=datetime.now(timezone.utc),
            turn_number=1,
            simulation_id="test-sim",
            details={"milestone_type": milestone_type}
        )

        assert event.event_type == "MILESTONE"
        assert event.details["milestone_type"] == milestone_type
        assert event.agent_id is None  # Milestone events should not have agent_id


def test_decision_event_schema():
    """T007: Validate DecisionEvent subclass schema."""
    event = DecisionEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        simulation_id="test-sim",
        agent_id="agent_bob",  # Required for decision events
        details={
            "decision_type": "strategy_change",
            "old_value": "conservative",
            "new_value": "aggressive"
        }
    )

    assert event.event_type == "DECISION"
    assert event.agent_id == "agent_bob"  # Must have agent_id
    assert event.details["decision_type"] == "strategy_change"
    assert event.details["old_value"] == "conservative"
    assert event.details["new_value"] == "aggressive"


def test_action_event_schema():
    """T008: Validate ActionEvent subclass schema."""
    event = ActionEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        simulation_id="test-sim",
        agent_id="agent_alice",  # Required for action events
        details={
            "action_type": "trade",
            "action_payload": {
                "partner": "agent_bob",
                "offer": {"gold": 100},
                "request": {"food": 50}
            }
        }
    )

    assert event.event_type == "ACTION"
    assert event.agent_id == "agent_alice"
    assert event.details["action_type"] == "trade"
    assert event.details["action_payload"]["partner"] == "agent_bob"


def test_state_event_schema():
    """T009: Validate StateEvent subclass schema."""
    event = StateEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        simulation_id="test-sim",
        agent_id="agent_alice",
        details={
            "variable_name": "wealth",
            "old_value": 1000,
            "new_value": 1150,
            "scope": "agent"
        }
    )

    assert event.event_type == "ENV"  # StateEvent is an alias for EnvEvent
    assert event.details["variable_name"] == "wealth"
    assert event.details["old_value"] == 1000
    assert event.details["new_value"] == 1150
    assert event.details["scope"] == "agent"


def test_detail_event_schema():
    """T010: Validate DetailEvent subclass schema."""
    event = DetailEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        simulation_id="test-sim",
        details={
            "calculation_type": "interest",
            "intermediate_values": {
                "principal": 1000,
                "rate": 0.05,
                "interest": 50,
                "new_total": 1050
            }
        }
    )

    assert event.event_type == "DETAIL"
    assert event.details["calculation_type"] == "interest"
    assert event.details["intermediate_values"]["principal"] == 1000


def test_system_event_schema():
    """T011: Validate SystemEvent subclass schema."""
    event = SystemEvent(
        event_id=str(ULID()),
        timestamp=datetime.now(timezone.utc),
        turn_number=1,
        simulation_id="test-sim",
        details={
            "error_type": "connection_timeout",
            "status": "retry",
            "retry_count": 1,
            "llm_model": "llama3"
        }
    )

    assert event.event_type == "SYSTEM"
    assert event.agent_id is None  # System events should not have agent_id
    assert event.details["error_type"] == "connection_timeout"
    assert event.details["status"] == "retry"
    assert event.details["retry_count"] == 1

    # Test valid status values
    valid_statuses = ["success", "failure", "retry", "warning"]
    for status in valid_statuses:
        event = SystemEvent(
            event_id=str(ULID()),
            timestamp=datetime.now(timezone.utc),
            turn_number=1,
            simulation_id="test-sim",
            details={"status": status}
        )
        assert event.details["status"] == status
