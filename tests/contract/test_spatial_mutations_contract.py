"""Contract tests for SpatialMutations interface.

Tests validate the contract requirements from specs/012-spatial-maps/contracts/spatial_mutations_contract.md
All mutation methods must be static, return new SpatialState, and preserve immutability.
"""

import pytest
from typing import Dict, Set, Tuple, Any

from llm_sim.infrastructure.spatial.mutations import SpatialMutations
from llm_sim.models.state import (
    SpatialState,
    LocationState,
    ConnectionState,
    NetworkState,
)


@pytest.fixture
def spatial_state() -> SpatialState:
    """Create spatial state for mutation testing."""
    return SpatialState(
        topology_type="grid",
        locations={
            "0,0": LocationState(id="0,0", attributes={"resource": 100}),
            "1,0": LocationState(id="1,0", attributes={"resource": 50}),
            "0,1": LocationState(id="0,1", attributes={"resource": 75}),
        },
        agent_positions={
            "agent_a": "0,0",
        },
        connections={
            ("0,0", "1,0"): ConnectionState(type="border", attributes={"cost": 10}),
        },
        networks={
            "default": NetworkState(
                name="default",
                edges={("0,0", "1,0"), ("0,0", "0,1")},
            )
        },
    )


class TestMoveAgent:
    """Contract tests for move_agent."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_positions = dict(spatial_state.agent_positions)
        SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")
        assert spatial_state.agent_positions == original_positions

    def test_updates_agent_position(self, spatial_state):
        """Update correctness: updates agent_positions[agent_name]."""
        new_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")
        assert new_state.agent_positions["agent_a"] == "1,0"

    def test_adds_agent_if_not_positioned(self, spatial_state):
        """Edge case: adds agent if not previously positioned."""
        new_state = SpatialMutations.move_agent(spatial_state, "new_agent", "1,0")
        assert new_state.agent_positions["new_agent"] == "1,0"

    def test_raises_error_for_invalid_location(self, spatial_state):
        """Error handling: raises ValueError if new_location not in locations."""
        with pytest.raises(ValueError, match="invalid location"):
            SpatialMutations.move_agent(spatial_state, "agent_a", "99,99")

    def test_preserves_other_fields(self, spatial_state):
        """Preservation: preserves locations, networks, connections."""
        new_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")
        assert new_state.locations == spatial_state.locations
        assert new_state.networks == spatial_state.networks
        assert new_state.connections == spatial_state.connections


class TestMoveAgentsBatch:
    """Contract tests for move_agents_batch."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        moves = {"agent_a": "1,0"}
        new_state = SpatialMutations.move_agents_batch(spatial_state, moves)
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_positions = dict(spatial_state.agent_positions)
        moves = {"agent_a": "1,0"}
        SpatialMutations.move_agents_batch(spatial_state, moves)
        assert spatial_state.agent_positions == original_positions

    def test_applies_all_moves_atomically(self, spatial_state):
        """Update correctness: applies all moves."""
        moves = {"agent_a": "1,0", "agent_b": "0,1"}
        new_state = SpatialMutations.move_agents_batch(spatial_state, moves)
        assert new_state.agent_positions["agent_a"] == "1,0"
        assert new_state.agent_positions["agent_b"] == "0,1"

    def test_validates_all_locations_before_applying(self, spatial_state):
        """Error handling: validates all before applying (no partial updates)."""
        moves = {"agent_a": "1,0", "agent_b": "99,99"}  # One invalid
        with pytest.raises(ValueError, match="invalid location"):
            SpatialMutations.move_agents_batch(spatial_state, moves)
        # Original unchanged
        assert spatial_state.agent_positions["agent_a"] == "0,0"

    def test_handles_empty_moves(self, spatial_state):
        """Edge case: handles empty moves dict."""
        new_state = SpatialMutations.move_agents_batch(spatial_state, {})
        assert new_state.agent_positions == spatial_state.agent_positions


class TestSetLocationAttribute:
    """Contract tests for set_location_attribute."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.set_location_attribute(spatial_state, "0,0", "resource", 150)
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_attrs = dict(spatial_state.locations["0,0"].attributes)
        SpatialMutations.set_location_attribute(spatial_state, "0,0", "resource", 150)
        assert spatial_state.locations["0,0"].attributes == original_attrs

    def test_updates_location_attribute(self, spatial_state):
        """Update correctness: updates location.attributes[key]."""
        new_state = SpatialMutations.set_location_attribute(spatial_state, "0,0", "resource", 150)
        assert new_state.locations["0,0"].attributes["resource"] == 150

    def test_raises_error_for_invalid_location(self, spatial_state):
        """Error handling: raises ValueError if location not found."""
        with pytest.raises(ValueError, match="not found|invalid"):
            SpatialMutations.set_location_attribute(spatial_state, "99,99", "resource", 150)

    def test_preserves_other_attributes(self, spatial_state):
        """Preservation: preserves other location attributes."""
        spatial_state = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(id="0,0", attributes={"resource": 100, "terrain": "plains"}),
            },
            agent_positions={},
            connections={},
            networks={"default": NetworkState(name="default", edges=set())},
        )
        new_state = SpatialMutations.set_location_attribute(spatial_state, "0,0", "resource", 150)
        assert new_state.locations["0,0"].attributes["terrain"] == "plains"

    def test_creates_new_location_state(self, spatial_state):
        """Update correctness: creates new LocationState instance."""
        new_state = SpatialMutations.set_location_attribute(spatial_state, "0,0", "resource", 150)
        assert new_state.locations["0,0"] is not spatial_state.locations["0,0"]


class TestUpdateLocationAttributes:
    """Contract tests for update_location_attributes."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        updates = {"resource": 200, "terrain": "forest"}
        new_state = SpatialMutations.update_location_attributes(spatial_state, "0,0", updates)
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_attrs = dict(spatial_state.locations["0,0"].attributes)
        updates = {"resource": 200}
        SpatialMutations.update_location_attributes(spatial_state, "0,0", updates)
        assert spatial_state.locations["0,0"].attributes == original_attrs

    def test_merges_updates_into_attributes(self, spatial_state):
        """Update correctness: merges updates into location.attributes."""
        updates = {"resource": 200, "terrain": "forest"}
        new_state = SpatialMutations.update_location_attributes(spatial_state, "0,0", updates)
        assert new_state.locations["0,0"].attributes["resource"] == 200
        assert new_state.locations["0,0"].attributes["terrain"] == "forest"

    def test_raises_error_for_invalid_location(self, spatial_state):
        """Error handling: raises ValueError if location not found."""
        with pytest.raises(ValueError, match="not found|invalid"):
            SpatialMutations.update_location_attributes(spatial_state, "99,99", {"key": "value"})

    def test_handles_empty_updates(self, spatial_state):
        """Edge case: handles empty updates dict."""
        new_state = SpatialMutations.update_location_attributes(spatial_state, "0,0", {})
        assert new_state.locations["0,0"].attributes == spatial_state.locations["0,0"].attributes


class TestAddConnection:
    """Contract tests for add_connection."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.add_connection(spatial_state, "1,0", "0,1", network="default")
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_edges = set(spatial_state.networks["default"].edges)
        SpatialMutations.add_connection(spatial_state, "1,0", "0,1", network="default")
        assert spatial_state.networks["default"].edges == original_edges

    def test_adds_edge_to_network(self, spatial_state):
        """Update correctness: adds (loc1, loc2) to network edges."""
        new_state = SpatialMutations.add_connection(spatial_state, "1,0", "0,1", network="default")
        # Edges stored as sorted tuples, so check both orderings
        edge = tuple(sorted(["1,0", "0,1"]))
        assert edge in new_state.networks["default"].edges

    def test_raises_error_for_invalid_location(self, spatial_state):
        """Error handling: raises ValueError if location not found."""
        with pytest.raises(ValueError, match="invalid location|not found"):
            SpatialMutations.add_connection(spatial_state, "0,0", "99,99", network="default")

    def test_raises_error_for_invalid_network(self, spatial_state):
        """Error handling: raises ValueError if network not found."""
        with pytest.raises(ValueError, match="network not found|invalid"):
            SpatialMutations.add_connection(spatial_state, "0,0", "1,0", network="invalid")

    def test_creates_connection_in_connections_dict(self, spatial_state):
        """Update correctness: creates connection with attributes if provided."""
        attributes = {"cost": 20}
        new_state = SpatialMutations.add_connection(spatial_state, "1,0", "0,1", network="default", attributes=attributes)
        # Check connection created in connections dict
        assert ("1,0", "0,1") in new_state.connections or ("0,1", "1,0") in new_state.connections


class TestRemoveConnection:
    """Contract tests for remove_connection."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.remove_connection(spatial_state, "0,0", "1,0", network="default")
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_edges = set(spatial_state.networks["default"].edges)
        SpatialMutations.remove_connection(spatial_state, "0,0", "1,0", network="default")
        assert spatial_state.networks["default"].edges == original_edges

    def test_removes_edge_from_network(self, spatial_state):
        """Update correctness: removes (loc1, loc2) from network edges."""
        new_state = SpatialMutations.remove_connection(spatial_state, "0,0", "1,0", network="default")
        assert ("0,0", "1,0") not in new_state.networks["default"].edges

    def test_is_idempotent_when_connection_does_not_exist(self, spatial_state):
        """Edge case: does not raise error if connection doesn't exist."""
        new_state = SpatialMutations.remove_connection(spatial_state, "1,0", "0,1", network="default")
        assert isinstance(new_state, SpatialState)

    def test_removes_from_connections_dict_if_present(self, spatial_state):
        """Update correctness: removes from connections dict."""
        new_state = SpatialMutations.remove_connection(spatial_state, "0,0", "1,0", network="default")
        assert ("0,0", "1,0") not in new_state.connections


class TestUpdateConnectionAttribute:
    """Contract tests for update_connection_attribute."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.update_connection_attribute(spatial_state, "0,0", "1,0", "cost", 20)
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_attrs = dict(spatial_state.connections[("0,0", "1,0")].attributes)
        SpatialMutations.update_connection_attribute(spatial_state, "0,0", "1,0", "cost", 20)
        assert spatial_state.connections[("0,0", "1,0")].attributes == original_attrs

    def test_updates_connection_attribute(self, spatial_state):
        """Update correctness: updates connection.attributes[key]."""
        new_state = SpatialMutations.update_connection_attribute(spatial_state, "0,0", "1,0", "cost", 20)
        assert new_state.connections[("0,0", "1,0")].attributes["cost"] == 20

    def test_raises_error_for_missing_connection(self, spatial_state):
        """Error handling: raises ValueError if connection not found."""
        with pytest.raises(ValueError, match="connection not found|invalid"):
            SpatialMutations.update_connection_attribute(spatial_state, "1,0", "0,1", "cost", 20)

    def test_preserves_other_connection_attributes(self, spatial_state):
        """Preservation: preserves other connection attributes."""
        spatial_state = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(id="0,0"),
                "1,0": LocationState(id="1,0"),
            },
            agent_positions={},
            connections={
                ("0,0", "1,0"): ConnectionState(type="border", attributes={"cost": 10, "speed": 5}),
            },
            networks={"default": NetworkState(name="default", edges={("0,0", "1,0")})},
        )
        new_state = SpatialMutations.update_connection_attribute(spatial_state, "0,0", "1,0", "cost", 20)
        assert new_state.connections[("0,0", "1,0")].attributes["speed"] == 5


class TestCreateNetwork:
    """Contract tests for create_network."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        new_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_networks = set(spatial_state.networks.keys())
        SpatialMutations.create_network(spatial_state, "rail", edges=set())
        assert set(spatial_state.networks.keys()) == original_networks

    def test_adds_network_to_networks_dict(self, spatial_state):
        """Update correctness: adds NetworkState to networks[network_name]."""
        new_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        assert "rail" in new_state.networks
        assert isinstance(new_state.networks["rail"], NetworkState)

    def test_raises_error_if_network_exists(self, spatial_state):
        """Error handling: raises ValueError if network_name already exists."""
        with pytest.raises(ValueError, match="already exists|duplicate"):
            SpatialMutations.create_network(spatial_state, "default", edges=set())

    def test_validates_edge_locations(self, spatial_state):
        """Error handling: validates all edge locations exist."""
        edges = {("0,0", "99,99")}
        with pytest.raises(ValueError, match="invalid location|not found"):
            SpatialMutations.create_network(spatial_state, "rail", edges=edges)

    def test_initializes_with_empty_edges_when_none(self, spatial_state):
        """Edge case: initializes with empty edges if edges=None."""
        new_state = SpatialMutations.create_network(spatial_state, "rail", edges=None)
        assert new_state.networks["rail"].edges == set()


class TestRemoveNetwork:
    """Contract tests for remove_network."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        # Add extra network first
        spatial_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        new_state = SpatialMutations.remove_network(spatial_state, "rail")
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        spatial_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        original_networks = set(spatial_state.networks.keys())
        SpatialMutations.remove_network(spatial_state, "rail")
        assert set(spatial_state.networks.keys()) == original_networks

    def test_removes_network_from_networks_dict(self, spatial_state):
        """Update correctness: removes networks[network_name]."""
        spatial_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        new_state = SpatialMutations.remove_network(spatial_state, "rail")
        assert "rail" not in new_state.networks

    def test_is_idempotent_when_network_does_not_exist(self, spatial_state):
        """Edge case: does not raise error if network doesn't exist."""
        new_state = SpatialMutations.remove_network(spatial_state, "nonexistent")
        assert isinstance(new_state, SpatialState)

    def test_raises_error_when_removing_default_network(self, spatial_state):
        """Error handling: raises ValueError if removing 'default' network."""
        with pytest.raises(ValueError, match="default.*cannot.*remove|protected"):
            SpatialMutations.remove_network(spatial_state, "default")

    def test_does_not_remove_connections(self, spatial_state):
        """Preservation: does not remove connections (independent)."""
        spatial_state = SpatialMutations.create_network(spatial_state, "rail", edges=set())
        original_connections = dict(spatial_state.connections)
        new_state = SpatialMutations.remove_network(spatial_state, "rail")
        assert new_state.connections == original_connections


class TestApplyToRegion:
    """Contract tests for apply_to_region."""

    def test_returns_new_spatial_state(self, spatial_state):
        """Return type: returns new SpatialState instance."""
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        new_state = SpatialMutations.apply_to_region(spatial_state, ["0,0"], update_fn)
        assert isinstance(new_state, SpatialState)
        assert new_state is not spatial_state

    def test_does_not_mutate_input(self, spatial_state):
        """Immutability: does not mutate input spatial_state."""
        original_attrs = dict(spatial_state.locations["0,0"].attributes)
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        SpatialMutations.apply_to_region(spatial_state, ["0,0"], update_fn)
        assert spatial_state.locations["0,0"].attributes == original_attrs

    def test_applies_update_function_to_all_locations(self, spatial_state):
        """Update correctness: applies update_fn to each location."""
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        new_state = SpatialMutations.apply_to_region(spatial_state, ["0,0", "1,0"], update_fn)
        assert new_state.locations["0,0"].attributes["resource"] == 200
        assert new_state.locations["1,0"].attributes["resource"] == 200

    def test_raises_error_for_invalid_location(self, spatial_state):
        """Error handling: raises ValueError if any location not found."""
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        with pytest.raises(ValueError, match="invalid location|not found"):
            SpatialMutations.apply_to_region(spatial_state, ["0,0", "99,99"], update_fn)

    def test_validates_all_locations_before_applying(self, spatial_state):
        """Error handling: validates all locations exist before applying."""
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        with pytest.raises(ValueError):
            SpatialMutations.apply_to_region(spatial_state, ["0,0", "99,99"], update_fn)
        # Original unchanged
        assert spatial_state.locations["0,0"].attributes["resource"] == 100

    def test_preserves_locations_not_in_list(self, spatial_state):
        """Preservation: preserves locations not in list unchanged."""
        def update_fn(loc: LocationState) -> Dict[str, Any]:
            return {"resource": 200}
        new_state = SpatialMutations.apply_to_region(spatial_state, ["0,0"], update_fn)
        assert new_state.locations["1,0"].attributes["resource"] == 50  # Unchanged
