"""Integration tests for Event API endpoints.

Tests validate end-to-end API functionality with real event data.
Based on quickstart.md Scenario 4: API query & filtering.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from ulid import ULID

from llm_sim.api.server import app
from llm_sim.infrastructure.events import EventWriter, VerbosityLevel
from llm_sim.infrastructure.events.builder import (
    create_milestone_event,
    create_action_event,
    create_decision_event,
)


@pytest_asyncio.fixture
async def populated_event_dir(tmp_path):
    """Create event directory with sample events."""
    output_dir = tmp_path / "output" / "api-test-sim-123"
    output_dir.mkdir(parents=True)

    # Create event writer
    event_writer = EventWriter(
        output_dir=output_dir,
        simulation_id="api-test-sim-123",
        verbosity=VerbosityLevel.ACTION
    )

    await event_writer.start()

    # Generate sample events
    # Turn 1
    event_writer.emit(create_milestone_event(
        simulation_id="api-test-sim-123",
        turn_number=1,
        milestone_type="turn_start",
        description="Turn 1 started"
    ))

    event_writer.emit(create_action_event(
        simulation_id="api-test-sim-123",
        turn_number=1,
        agent_id="agent_alice",
        action_type="trade",
        action_payload={"partner": "agent_bob", "amount": 100},
        description="Alice traded with Bob"
    ))

    event_writer.emit(create_milestone_event(
        simulation_id="api-test-sim-123",
        turn_number=1,
        milestone_type="turn_end",
        description="Turn 1 ended"
    ))

    # Turn 2
    event_writer.emit(create_milestone_event(
        simulation_id="api-test-sim-123",
        turn_number=2,
        milestone_type="turn_start",
        description="Turn 2 started"
    ))

    event_writer.emit(create_action_event(
        simulation_id="api-test-sim-123",
        turn_number=2,
        agent_id="agent_bob",
        action_type="invest",
        action_payload={"amount": 50},
        description="Bob invested 50"
    ))

    event_writer.emit(create_milestone_event(
        simulation_id="api-test-sim-123",
        turn_number=2,
        milestone_type="turn_end",
        description="Turn 2 ended"
    ))

    # Allow events to be written
    await asyncio.sleep(0.1)
    await event_writer.stop(timeout=5.0)

    return tmp_path / "output"


@pytest.mark.asyncio
async def test_api_filter_by_agent_id(populated_event_dir, monkeypatch):
    """T020: Verify API returns filtered events by agent_id."""
    # Set app state to use test directory
    app.state.output_root = populated_event_dir

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/simulations/api-test-sim-123/events",
            params={"agent_ids": ["agent_alice"]}
        )

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert len(data["events"]) > 0

        # Verify all returned events are from agent_alice
        for event in data["events"]:
            if "agent_id" in event and event["agent_id"]:
                assert event["agent_id"] == "agent_alice", \
                    f"Expected agent_alice, got {event['agent_id']}"


@pytest.mark.asyncio
async def test_api_aggregates_rotated_files(tmp_path, monkeypatch):
    """T021: Verify API aggregates events across rotated files."""
    output_dir = tmp_path / "output" / "rotation-sim"
    output_dir.mkdir(parents=True)

    # Create multiple event files (simulating rotation)
    events_file_1 = output_dir / "events_2025-01-01_10-00-00.jsonl"
    events_file_2 = output_dir / "events.jsonl"

    # Write events to first file
    with open(events_file_1, "w") as f:
        event1 = create_milestone_event(
            simulation_id="rotation-sim",
            turn_number=1,
            milestone_type="turn_start"
        )
        f.write(json.dumps(event1.model_dump(mode="json")) + "\n")

    # Write events to second file
    with open(events_file_2, "w") as f:
        event2 = create_milestone_event(
            simulation_id="rotation-sim",
            turn_number=2,
            milestone_type="turn_start"
        )
        f.write(json.dumps(event2.model_dump(mode="json")) + "\n")

    # Set app state to use test directory
    app.state.output_root = tmp_path / "output"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/simulations/rotation-sim/events")

        assert response.status_code == 200
        data = response.json()

        # Verify events from both files are returned
        assert len(data["events"]) == 2, \
            f"Expected 2 events from rotated files, got {len(data['events'])}"


@pytest.mark.asyncio
async def test_api_filter_by_turn_range(populated_event_dir, monkeypatch):
    """T022: Verify API filtering by turn range."""
    # Set app state to use test directory
    app.state.output_root = populated_event_dir

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/simulations/api-test-sim-123/events",
            params={"turn_start": 2, "turn_end": 2}
        )

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert len(data["events"]) > 0

        # Verify all events are from turn 2
        for event in data["events"]:
            assert event["turn_number"] == 2, \
                f"Expected turn 2, got turn {event['turn_number']}"


@pytest.mark.asyncio
async def test_api_pagination(populated_event_dir, monkeypatch):
    """Verify API pagination with limit and offset."""
    # Set app state to use test directory
    app.state.output_root = populated_event_dir

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get first page
        response1 = await client.get(
            "/simulations/api-test-sim-123/events",
            params={"limit": 2, "offset": 0}
        )

        assert response1.status_code == 200
        data1 = response1.json()

        # Get second page
        response2 = await client.get(
            "/simulations/api-test-sim-123/events",
            params={"limit": 2, "offset": 2}
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Verify different events returned
        if len(data1["events"]) > 0 and len(data2["events"]) > 0:
            event_ids_1 = {e["event_id"] for e in data1["events"]}
            event_ids_2 = {e["event_id"] for e in data2["events"]}

            assert event_ids_1.isdisjoint(event_ids_2), \
                "Pagination should return different events on different pages"


@pytest.mark.asyncio
async def test_api_list_simulations(populated_event_dir, monkeypatch):
    """Verify API lists all simulations with event streams."""
    # Set app state to use test directory
    app.state.output_root = populated_event_dir

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/simulations")

        assert response.status_code == 200
        data = response.json()

        assert "simulations" in data
        assert len(data["simulations"]) > 0

        # Verify our test simulation is listed
        sim_ids = [sim["id"] for sim in data["simulations"]]
        assert "api-test-sim-123" in sim_ids
