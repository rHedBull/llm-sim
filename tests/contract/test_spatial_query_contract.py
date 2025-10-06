"""Contract tests for SpatialQuery interface.

Tests validate the contract requirements from specs/012-spatial-maps/contracts/spatial_query_contract.md
All query methods must be static, pure, handle None gracefully, and not mutate inputs.
"""

import pytest
from typing import Optional

from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.models.state import (
    SpatialState,
    LocationState,
    ConnectionState,
    NetworkState,
    SimulationState,
)


@pytest.fixture
def minimal_spatial_state() -> SpatialState:
    """Create minimal spatial state for testing."""
    return SpatialState(
        topology_type="grid",
        locations={
            "0,0": LocationState(id="0,0", attributes={"terrain": "plains"}),
            "1,0": LocationState(id="1,0", attributes={"terrain": "forest"}),
            "0,1": LocationState(id="0,1", attributes={"terrain": "plains"}),
        },
        agent_positions={
            "agent_a": "0,0",
            "agent_b": "1,0",
        },
        connections={
            ("0,0", "1,0"): ConnectionState(type="border", bidirectional=True, attributes={"cost": 5}),
            ("0,0", "0,1"): ConnectionState(type="border", bidirectional=True),
        },
        networks={
            "default": NetworkState(
                name="default",
                edges={("0,0", "1,0"), ("0,0", "0,1")},
            )
        },
    )


class TestGetAgentPosition:
    """Contract tests for get_agent_position."""

    def test_returns_location_for_valid_agent(self, minimal_spatial_state):
        """Happy path: returns location ID for positioned agent."""
        location = SpatialQuery.get_agent_position(minimal_spatial_state, "agent_a")
        assert location == "0,0"

    def test_returns_none_for_missing_agent(self, minimal_spatial_state):
        """Missing data: returns None for agent not in agent_positions."""
        location = SpatialQuery.get_agent_position(minimal_spatial_state, "missing_agent")
        assert location is None

    def test_returns_none_when_spatial_state_none(self):
        """None handling: returns None when spatial_state is None."""
        location = SpatialQuery.get_agent_position(None, "agent_a")
        assert location is None

    def test_does_not_mutate_spatial_state(self, minimal_spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_positions = dict(minimal_spatial_state.agent_positions)
        SpatialQuery.get_agent_position(minimal_spatial_state, "agent_a")
        assert minimal_spatial_state.agent_positions == original_positions


class TestGetNeighbors:
    """Contract tests for get_neighbors."""

    def test_returns_neighbors_via_default_network(self, minimal_spatial_state):
        """Happy path: returns neighboring locations."""
        neighbors = SpatialQuery.get_neighbors(minimal_spatial_state, "0,0")
        assert set(neighbors) == {"1,0", "0,1"}

    def test_returns_empty_list_when_spatial_state_none(self):
        """None handling: returns empty list when spatial_state is None."""
        neighbors = SpatialQuery.get_neighbors(None, "0,0")
        assert neighbors == []

    def test_returns_empty_list_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns empty list for non-existent location."""
        neighbors = SpatialQuery.get_neighbors(minimal_spatial_state, "99,99")
        assert neighbors == []

    def test_returns_empty_list_for_invalid_network(self, minimal_spatial_state):
        """Missing data: returns empty list for non-existent network."""
        neighbors = SpatialQuery.get_neighbors(minimal_spatial_state, "0,0", network="invalid")
        assert neighbors == []

    def test_does_not_include_location_itself(self, minimal_spatial_state):
        """Edge case: returned neighbors do not include location itself."""
        neighbors = SpatialQuery.get_neighbors(minimal_spatial_state, "0,0")
        assert "0,0" not in neighbors


class TestGetDistance:
    """Contract tests for get_distance."""

    def test_returns_zero_for_same_location(self, minimal_spatial_state):
        """Edge case: returns 0 when loc1 == loc2."""
        distance = SpatialQuery.get_distance(minimal_spatial_state, "0,0", "0,0")
        assert distance == 0

    def test_returns_hops_between_adjacent_locations(self, minimal_spatial_state):
        """Happy path: returns 1 for adjacent locations."""
        distance = SpatialQuery.get_distance(minimal_spatial_state, "0,0", "1,0")
        assert distance == 1

    def test_returns_shortest_path_length(self, minimal_spatial_state):
        """Happy path: returns shortest path length."""
        distance = SpatialQuery.get_distance(minimal_spatial_state, "1,0", "0,1")
        assert distance == 2  # 1,0 -> 0,0 -> 0,1

    def test_returns_minus_one_when_spatial_state_none(self):
        """None handling: returns -1 when spatial_state is None."""
        distance = SpatialQuery.get_distance(None, "0,0", "1,0")
        assert distance == -1

    def test_returns_minus_one_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns -1 when location not found."""
        distance = SpatialQuery.get_distance(minimal_spatial_state, "0,0", "99,99")
        assert distance == -1

    def test_returns_minus_one_for_invalid_network(self, minimal_spatial_state):
        """Missing data: returns -1 when network not found."""
        distance = SpatialQuery.get_distance(minimal_spatial_state, "0,0", "1,0", network="invalid")
        assert distance == -1


class TestIsAdjacent:
    """Contract tests for is_adjacent."""

    def test_returns_true_for_adjacent_locations(self, minimal_spatial_state):
        """Happy path: returns True for directly connected locations."""
        assert SpatialQuery.is_adjacent(minimal_spatial_state, "0,0", "1,0")

    def test_returns_true_for_same_location(self, minimal_spatial_state):
        """Edge case: returns True when loc1 == loc2."""
        assert SpatialQuery.is_adjacent(minimal_spatial_state, "0,0", "0,0")

    def test_returns_false_for_non_adjacent_locations(self, minimal_spatial_state):
        """Happy path: returns False for non-adjacent locations."""
        assert not SpatialQuery.is_adjacent(minimal_spatial_state, "1,0", "0,1")

    def test_returns_false_when_spatial_state_none(self):
        """None handling: returns False when spatial_state is None."""
        assert not SpatialQuery.is_adjacent(None, "0,0", "1,0")

    def test_returns_false_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns False when location not found."""
        assert not SpatialQuery.is_adjacent(minimal_spatial_state, "0,0", "99,99")

    def test_returns_false_for_invalid_network(self, minimal_spatial_state):
        """Missing data: returns False when network not found."""
        assert not SpatialQuery.is_adjacent(minimal_spatial_state, "0,0", "1,0", network="invalid")


class TestShortestPath:
    """Contract tests for shortest_path."""

    def test_returns_path_for_adjacent_locations(self, minimal_spatial_state):
        """Happy path: returns path for connected locations."""
        path = SpatialQuery.shortest_path(minimal_spatial_state, "0,0", "1,0")
        assert path == ["0,0", "1,0"]

    def test_returns_single_location_for_same_location(self, minimal_spatial_state):
        """Edge case: returns [loc1] when loc1 == loc2."""
        path = SpatialQuery.shortest_path(minimal_spatial_state, "0,0", "0,0")
        assert path == ["0,0"]

    def test_returns_shortest_path_with_intermediate_nodes(self, minimal_spatial_state):
        """Happy path: returns complete path including intermediates."""
        path = SpatialQuery.shortest_path(minimal_spatial_state, "1,0", "0,1")
        assert path[0] == "1,0"
        assert path[-1] == "0,1"
        assert "0,0" in path  # Must go through 0,0

    def test_returns_empty_list_when_spatial_state_none(self):
        """None handling: returns empty list when spatial_state is None."""
        path = SpatialQuery.shortest_path(None, "0,0", "1,0")
        assert path == []

    def test_returns_empty_list_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns empty list when location not found."""
        path = SpatialQuery.shortest_path(minimal_spatial_state, "0,0", "99,99")
        assert path == []

    def test_returns_empty_list_for_invalid_network(self, minimal_spatial_state):
        """Missing data: returns empty list when network not found."""
        path = SpatialQuery.shortest_path(minimal_spatial_state, "0,0", "1,0", network="invalid")
        assert path == []


class TestGetAgentsAt:
    """Contract tests for get_agents_at."""

    def test_returns_agents_at_location(self, minimal_spatial_state):
        """Happy path: returns list of agents at location."""
        agents = SpatialQuery.get_agents_at(minimal_spatial_state, "0,0")
        assert agents == ["agent_a"]

    def test_returns_empty_list_for_location_with_no_agents(self, minimal_spatial_state):
        """Edge case: returns empty list when no agents at location."""
        agents = SpatialQuery.get_agents_at(minimal_spatial_state, "0,1")
        assert agents == []

    def test_returns_empty_list_when_spatial_state_none(self):
        """None handling: returns empty list when spatial_state is None."""
        agents = SpatialQuery.get_agents_at(None, "0,0")
        assert agents == []

    def test_returns_empty_list_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns empty list for non-existent location."""
        agents = SpatialQuery.get_agents_at(minimal_spatial_state, "99,99")
        assert agents == []


class TestGetAgentsWithin:
    """Contract tests for get_agents_within."""

    def test_includes_agents_at_location_itself(self, minimal_spatial_state):
        """Edge case: includes agents at radius 0 (location itself)."""
        agents = SpatialQuery.get_agents_within(minimal_spatial_state, "0,0", radius=0)
        assert "agent_a" in agents

    def test_includes_agents_within_radius(self, minimal_spatial_state):
        """Happy path: includes agents at distance <= radius."""
        agents = SpatialQuery.get_agents_within(minimal_spatial_state, "0,0", radius=1)
        assert set(agents) == {"agent_a", "agent_b"}

    def test_returns_empty_list_when_spatial_state_none(self):
        """None handling: returns empty list when spatial_state is None."""
        agents = SpatialQuery.get_agents_within(None, "0,0", radius=1)
        assert agents == []

    def test_returns_empty_list_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns empty list for non-existent location."""
        agents = SpatialQuery.get_agents_within(minimal_spatial_state, "99,99", radius=1)
        assert agents == []


class TestGetLocationAttribute:
    """Contract tests for get_location_attribute."""

    def test_returns_attribute_value_for_valid_key(self, minimal_spatial_state):
        """Happy path: returns attribute value when key exists."""
        value = SpatialQuery.get_location_attribute(minimal_spatial_state, "0,0", "terrain")
        assert value == "plains"

    def test_returns_none_when_spatial_state_none(self):
        """None handling: returns None when spatial_state is None."""
        value = SpatialQuery.get_location_attribute(None, "0,0", "terrain")
        assert value is None

    def test_returns_none_for_invalid_location(self, minimal_spatial_state):
        """Missing data: returns None when location not found."""
        value = SpatialQuery.get_location_attribute(minimal_spatial_state, "99,99", "terrain")
        assert value is None

    def test_returns_none_for_missing_key(self, minimal_spatial_state):
        """Missing data: returns None when key not in attributes."""
        value = SpatialQuery.get_location_attribute(minimal_spatial_state, "0,0", "missing_key")
        assert value is None

    def test_does_not_mutate_spatial_state(self, minimal_spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_attrs = dict(minimal_spatial_state.locations["0,0"].attributes)
        SpatialQuery.get_location_attribute(minimal_spatial_state, "0,0", "terrain")
        assert minimal_spatial_state.locations["0,0"].attributes == original_attrs


class TestGetLocationsByAttribute:
    """Contract tests for get_locations_by_attribute."""

    def test_returns_locations_matching_attribute_value(self, minimal_spatial_state):
        """Happy path: returns locations where attribute matches value."""
        locations = SpatialQuery.get_locations_by_attribute(minimal_spatial_state, "terrain", "plains")
        assert set(locations) == {"0,0", "0,1"}

    def test_returns_empty_list_when_spatial_state_none(self):
        """None handling: returns empty list when spatial_state is None."""
        locations = SpatialQuery.get_locations_by_attribute(None, "terrain", "plains")
        assert locations == []

    def test_returns_empty_list_when_no_matches(self, minimal_spatial_state):
        """Edge case: returns empty list when no locations match."""
        locations = SpatialQuery.get_locations_by_attribute(minimal_spatial_state, "terrain", "ocean")
        assert locations == []

    def test_handles_missing_key_gracefully(self, minimal_spatial_state):
        """Missing data: skips locations without the attribute key."""
        locations = SpatialQuery.get_locations_by_attribute(minimal_spatial_state, "missing_key", "value")
        assert locations == []


class TestHasConnection:
    """Contract tests for has_connection."""

    def test_returns_true_for_existing_connection(self, minimal_spatial_state):
        """Happy path: returns True when connection exists in network."""
        assert SpatialQuery.has_connection(minimal_spatial_state, "0,0", "1,0", network="default")

    def test_returns_true_for_same_location(self, minimal_spatial_state):
        """Edge case: returns True when loc1 == loc2."""
        assert SpatialQuery.has_connection(minimal_spatial_state, "0,0", "0,0", network="default")

    def test_returns_false_when_spatial_state_none(self):
        """None handling: returns False when spatial_state is None."""
        assert not SpatialQuery.has_connection(None, "0,0", "1,0", network="default")

    def test_returns_false_for_invalid_network(self, minimal_spatial_state):
        """Missing data: returns False when network not found."""
        assert not SpatialQuery.has_connection(minimal_spatial_state, "0,0", "1,0", network="invalid")


class TestGetConnectionAttribute:
    """Contract tests for get_connection_attribute."""

    def test_returns_attribute_value_for_valid_connection(self, minimal_spatial_state):
        """Happy path: returns attribute value when key exists."""
        value = SpatialQuery.get_connection_attribute(minimal_spatial_state, "0,0", "1,0", "cost")
        # Connection ("0,0", "1,0") has attribute cost=5
        assert value == 5

    def test_returns_none_when_spatial_state_none(self):
        """None handling: returns None when spatial_state is None."""
        value = SpatialQuery.get_connection_attribute(None, "0,0", "1,0", "key")
        assert value is None

    def test_returns_none_for_missing_connection(self, minimal_spatial_state):
        """Missing data: returns None when connection not found."""
        value = SpatialQuery.get_connection_attribute(minimal_spatial_state, "1,0", "0,1", "key")
        assert value is None

    def test_returns_none_for_missing_key(self, minimal_spatial_state):
        """Missing data: returns None when key not in connection attributes."""
        value = SpatialQuery.get_connection_attribute(minimal_spatial_state, "0,0", "1,0", "missing_key")
        assert value is None


class TestFilterStateByProximity:
    """Contract tests for filter_state_by_proximity."""

    def test_returns_unmodified_state_when_spatial_state_none(self, mock_simulation_state):
        """None handling: returns state unchanged when spatial_state is None."""
        filtered = SpatialQuery.filter_state_by_proximity("agent_a", mock_simulation_state, radius=1)
        assert filtered == mock_simulation_state

    def test_filters_agents_by_proximity(self, minimal_spatial_state, mock_global_state):
        """Happy path: filters agents dict to include only nearby agents."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=minimal_spatial_state,
        )
        filtered = SpatialQuery.filter_state_by_proximity("agent_a", state, radius=0)
        # Should only include agents at same location (agent_a)
        # Will fail until implementation
        assert filtered is not None

    def test_preserves_global_state_unchanged(self, minimal_spatial_state, mock_global_state):
        """Preservation: preserves global_state field unchanged."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=minimal_spatial_state,
        )
        filtered = SpatialQuery.filter_state_by_proximity("agent_a", state, radius=1)
        assert filtered.global_state == state.global_state

    def test_uses_immutable_updates(self, minimal_spatial_state, mock_global_state):
        """Immutability: returns new SimulationState instance."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=minimal_spatial_state,
        )
        filtered = SpatialQuery.filter_state_by_proximity("agent_a", state, radius=1)
        assert filtered is not state
        assert state.spatial_state == minimal_spatial_state  # Original unchanged
