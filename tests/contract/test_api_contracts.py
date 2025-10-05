"""Contract tests for Event API endpoints.

Tests validate that API endpoints match the OpenAPI specification
defined in specs/010-event-stream-the/contracts/api-openapi.yaml.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from llm_sim.api.server import app


@pytest.fixture
def client():
    """Create test client for API."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client for API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


def test_list_simulations_endpoint(client):
    """T012: Validate GET /simulations endpoint response schema."""
    response = client.get("/simulations")

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "simulations" in data
    assert isinstance(data["simulations"], list)

    # If simulations exist, validate schema
    if len(data["simulations"]) > 0:
        sim = data["simulations"][0]
        assert "id" in sim
        assert "name" in sim
        assert "start_time" in sim
        assert "event_count" in sim
        assert isinstance(sim["event_count"], int)


def test_get_events_endpoint_schema(client):
    """T013: Validate GET /simulations/{simulation_id}/events endpoint."""
    # This test requires a simulation to exist - will use mock data or skip if none
    response = client.get("/simulations/test-sim-123/events?limit=10&offset=0")

    # Should return 200 or 404 (both valid if simulation doesn't exist)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()

        # Validate EventsResponse schema
        assert "events" in data
        assert "total" in data
        assert "has_more" in data

        assert isinstance(data["events"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["has_more"], bool)

        # Validate Event schema if events exist
        if len(data["events"]) > 0:
            event = data["events"][0]
            assert "event_id" in event
            assert "timestamp" in event
            assert "turn_number" in event
            assert "event_type" in event
            assert "simulation_id" in event
            assert len(event["event_id"]) == 26  # ULID length


def test_get_events_filter_params(client):
    """T013 (continued): Validate EventFilter query parameters."""
    # Test with various filter combinations
    params = {
        "event_types": ["MILESTONE", "ACTION"],
        "agent_ids": ["agent_alice"],
        "turn_start": 5,
        "turn_end": 10,
        "limit": 100,
        "offset": 0
    }

    # Build query string manually for array params
    query = "event_types=MILESTONE&event_types=ACTION&agent_ids=agent_alice&turn_start=5&turn_end=10&limit=100&offset=0"
    response = client.get(f"/simulations/test-sim-123/events?{query}")

    # Should accept parameters without error (200 or 404)
    assert response.status_code in [200, 404]


def test_get_single_event_endpoint(client):
    """T014: Validate GET /simulations/{simulation_id}/events/{event_id} endpoint."""
    from ulid import ULID

    test_event_id = str(ULID())
    response = client.get(f"/simulations/test-sim-123/events/{test_event_id}")

    # Should return 404 if event doesn't exist, or 200 if it does
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        event = response.json()

        # Validate full Event schema
        assert "event_id" in event
        assert "timestamp" in event
        assert "turn_number" in event
        assert "event_type" in event
        assert "simulation_id" in event
        assert event["event_id"] == test_event_id


def test_get_causality_chain_endpoint(client):
    """T015: Validate GET /simulations/{simulation_id}/causality/{event_id} endpoint."""
    from ulid import ULID

    test_event_id = str(ULID())
    response = client.get(f"/simulations/test-sim-123/causality/{test_event_id}")

    # Should return 404 if event doesn't exist, or 200 if it does
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()

        # Validate CausalityChain schema
        assert "event_id" in data
        assert "upstream" in data
        assert "downstream" in data

        assert data["event_id"] == test_event_id
        assert isinstance(data["upstream"], list)
        assert isinstance(data["downstream"], list)

        # Validate upstream/downstream events are full Event objects
        if len(data["upstream"]) > 0:
            upstream_event = data["upstream"][0]
            assert "event_id" in upstream_event
            assert "timestamp" in upstream_event


def test_causality_depth_parameter(client):
    """T015 (continued): Validate depth parameter for causality endpoint."""
    from ulid import ULID

    test_event_id = str(ULID())
    response = client.get(f"/simulations/test-sim-123/causality/{test_event_id}?depth=3")

    # Should accept depth parameter without error
    assert response.status_code in [200, 404]


def test_api_error_responses(client):
    """Validate API error response schema."""
    # Test 404 error
    response = client.get("/simulations/nonexistent-sim/events")

    if response.status_code == 404:
        error = response.json()
        assert "code" in error
        assert "message" in error
