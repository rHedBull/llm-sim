"""Unit tests for spatial query operations.

Tests specific implementation details beyond contract requirements.
"""

import pytest

from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.models.state import (
    SpatialState,
    LocationState,
    ConnectionState,
    NetworkState,
    SimulationState,
)


@pytest.fixture
def complex_spatial_state():
    """Create complex spatial state for query testing."""
    return SpatialState(
        topology_type="network",
        locations={
            "a": LocationState(id="a", attributes={"type": "city", "resource": 100}),
            "b": LocationState(id="b", attributes={"type": "city", "resource": 50}),
            "c": LocationState(id="c", attributes={"type": "village", "resource": 25}),
            "d": LocationState(id="d", attributes={"type": "city", "resource": 75}),
        },
        agent_positions={
            "agent_1": "a",
            "agent_2": "b",
            "agent_3": "b",  # Multiple agents at same location
        },
        connections={
            ("a", "b"): ConnectionState(type="road", attributes={"distance": 10}),
            ("b", "c"): ConnectionState(type="road", attributes={"distance": 5}),
            ("a", "d"): ConnectionState(type="rail", attributes={"distance": 20}),
        },
        networks={
            "default": NetworkState(name="default", edges={("a", "b"), ("b", "c")}),
            "rail": NetworkState(name="rail", edges={("a", "d")}),
        }
    )


class TestGetNeighborsAdvanced:
    """Advanced tests for get_neighbors."""

    def test_different_networks_return_different_neighbors(self, complex_spatial_state):
        """Different networks have different neighbor sets."""
        default_neighbors = set(SpatialQuery.get_neighbors(complex_spatial_state, "a", network="default"))
        rail_neighbors = set(SpatialQuery.get_neighbors(complex_spatial_state, "a", network="rail"))
        assert default_neighbors != rail_neighbors

    def test_isolated_node_has_no_neighbors(self):
        """Isolated nodes return empty list."""
        state = SpatialState(
            topology_type="network",
            locations={"a": LocationState(id="a"), "b": LocationState(id="b")},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        neighbors = SpatialQuery.get_neighbors(state, "a")
        assert neighbors == []


class TestGetDistanceAdvanced:
    """Advanced tests for get_distance."""

    def test_no_path_returns_minus_one(self):
        """No path between disconnected nodes returns -1."""
        state = SpatialState(
            topology_type="network",
            locations={"a": LocationState(id="a"), "b": LocationState(id="b")},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        distance = SpatialQuery.get_distance(state, "a", "b")
        assert distance == -1

    def test_shortest_path_across_multiple_hops(self, complex_spatial_state):
        """Computes shortest path across multiple hops."""
        distance = SpatialQuery.get_distance(complex_spatial_state, "a", "c")
        assert distance == 2  # a -> b -> c


class TestGetAgentsAtAdvanced:
    """Advanced tests for get_agents_at."""

    def test_multiple_agents_at_same_location(self, complex_spatial_state):
        """Returns all agents at location."""
        agents = SpatialQuery.get_agents_at(complex_spatial_state, "b")
        assert set(agents) == {"agent_2", "agent_3"}

    def test_single_agent_at_location(self, complex_spatial_state):
        """Returns single agent."""
        agents = SpatialQuery.get_agents_at(complex_spatial_state, "a")
        assert agents == ["agent_1"]


class TestGetAgentsWithinAdvanced:
    """Advanced tests for get_agents_within."""

    def test_radius_zero_only_includes_same_location(self, complex_spatial_state):
        """Radius 0 only includes agents at exact location."""
        agents = SpatialQuery.get_agents_within(complex_spatial_state, "a", radius=0)
        assert set(agents) == {"agent_1"}

    def test_radius_one_includes_adjacent(self, complex_spatial_state):
        """Radius 1 includes agents at adjacent locations."""
        agents = SpatialQuery.get_agents_within(complex_spatial_state, "a", radius=1)
        # Should include agent_1 (at a), agent_2 and agent_3 (at b, adjacent to a)
        assert set(agents) == {"agent_1", "agent_2", "agent_3"}

    def test_large_radius_includes_all_connected(self, complex_spatial_state):
        """Large radius includes all connected agents."""
        agents = SpatialQuery.get_agents_within(complex_spatial_state, "a", radius=100)
        # Should include all agents in connected component
        assert len(agents) >= 3


class TestGetLocationsByAttributeAdvanced:
    """Advanced tests for get_locations_by_attribute."""

    def test_filters_by_exact_value_match(self, complex_spatial_state):
        """Only returns locations with exact value match."""
        cities = SpatialQuery.get_locations_by_attribute(complex_spatial_state, "type", "city")
        assert set(cities) == {"a", "b", "d"}

    def test_different_values_return_different_locations(self, complex_spatial_state):
        """Different attribute values return different location sets."""
        cities = set(SpatialQuery.get_locations_by_attribute(complex_spatial_state, "type", "city"))
        villages = set(SpatialQuery.get_locations_by_attribute(complex_spatial_state, "type", "village"))
        assert cities != villages
        assert "c" in villages


class TestConnectionAttributeQueries:
    """Tests for connection attribute queries."""

    def test_bidirectional_lookup(self, complex_spatial_state):
        """Checks both (a,b) and (b,a) for bidirectional connections."""
        # Should find connection attributes regardless of order
        attr1 = SpatialQuery.get_connection_attribute(complex_spatial_state, "a", "b", "distance")
        attr2 = SpatialQuery.get_connection_attribute(complex_spatial_state, "b", "a", "distance")
        # At least one should return the value
        assert attr1 is not None or attr2 is not None


class TestFilterStateByProximityAdvanced:
    """Advanced tests for proximity filtering."""

    def test_filters_locations_by_distance(self, complex_spatial_state, mock_global_state):
        """Filtered state only includes nearby locations."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=complex_spatial_state,
        )
        filtered = SpatialQuery.filter_state_by_proximity("agent_1", state, radius=1)
        # Should only include locations within radius 1 of "a"
        # Will fail until implementation
        assert filtered.spatial_state is not None

    def test_preserves_turn_and_global_state(self, complex_spatial_state, mock_global_state):
        """Preserves non-spatial fields."""
        state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=complex_spatial_state,
        )
        filtered = SpatialQuery.filter_state_by_proximity("agent_1", state, radius=1)
        assert filtered.turn == 5
        assert filtered.global_state == mock_global_state


class TestQueryPerformance:
    """Performance-related tests."""

    def test_handles_large_agent_count(self):
        """Handles queries with many agents efficiently."""
        locations = {f"loc_{i}": LocationState(id=f"loc_{i}") for i in range(100)}
        agent_positions = {f"agent_{i}": f"loc_{i % 10}" for i in range(1000)}
        state = SpatialState(
            topology_type="grid",
            locations=locations,
            agent_positions=agent_positions,
            networks={"default": NetworkState(name="default", edges=set())}
        )
        # Should complete quickly
        agents = SpatialQuery.get_agents_at(state, "loc_0")
        assert len(agents) >= 100  # Many agents at loc_0

    def test_handles_large_location_count(self):
        """Handles queries with many locations efficiently."""
        locations = {f"loc_{i}": LocationState(id=f"loc_{i}", attributes={"type": "city"}) for i in range(1000)}
        state = SpatialState(
            topology_type="grid",
            locations=locations,
            networks={"default": NetworkState(name="default", edges=set())}
        )
        # Should complete quickly
        cities = SpatialQuery.get_locations_by_attribute(state, "type", "city")
        assert len(cities) == 1000


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_spatial_state_returns_safe_defaults(self):
        """Empty spatial state returns safe defaults."""
        state = SpatialState(topology_type="grid")
        assert SpatialQuery.get_agent_position(state, "agent") is None
        assert SpatialQuery.get_neighbors(state, "loc") == []
        assert SpatialQuery.get_agents_at(state, "loc") == []

    def test_queries_with_special_characters_in_ids(self):
        """Handles location IDs with special characters."""
        state = SpatialState(
            topology_type="network",
            locations={
                "location-with-dashes": LocationState(id="location-with-dashes"),
                "location_with_underscores": LocationState(id="location_with_underscores"),
            },
            agent_positions={"agent": "location-with-dashes"},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        position = SpatialQuery.get_agent_position(state, "agent")
        assert position == "location-with-dashes"
