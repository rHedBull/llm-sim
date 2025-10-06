"""Unit tests for spatial mutation operations.

Tests specific implementation details beyond contract requirements.
"""

import pytest

from llm_sim.infrastructure.spatial.mutations import SpatialMutations
from llm_sim.models.state import (
    SpatialState,
    LocationState,
    ConnectionState,
    NetworkState,
)


@pytest.fixture
def mutable_spatial_state():
    """Create spatial state for mutation testing."""
    return SpatialState(
        topology_type="network",
        locations={
            "a": LocationState(id="a", attributes={"resource": 100, "population": 1000}),
            "b": LocationState(id="b", attributes={"resource": 50, "population": 500}),
            "c": LocationState(id="c", attributes={"resource": 25, "population": 250}),
        },
        agent_positions={
            "agent_1": "a",
            "agent_2": "b",
        },
        connections={
            ("a", "b"): ConnectionState(type="road", attributes={"cost": 10, "speed": 5}),
        },
        networks={
            "default": NetworkState(name="default", edges={("a", "b"), ("b", "c")}),
        }
    )


class TestMoveAgentAdvanced:
    """Advanced tests for move_agent."""

    def test_moving_agent_updates_only_that_agent(self, mutable_spatial_state):
        """Moving one agent doesn't affect others."""
        new_state = SpatialMutations.move_agent(mutable_spatial_state, "agent_1", "b")
        assert new_state.agent_positions["agent_1"] == "b"
        assert new_state.agent_positions["agent_2"] == "b"  # Unchanged

    def test_moving_to_same_location_is_idempotent(self, mutable_spatial_state):
        """Moving to same location is valid."""
        new_state = SpatialMutations.move_agent(mutable_spatial_state, "agent_1", "a")
        assert new_state.agent_positions["agent_1"] == "a"

    def test_adding_new_agent(self, mutable_spatial_state):
        """Can add new agent via move_agent."""
        new_state = SpatialMutations.move_agent(mutable_spatial_state, "new_agent", "c")
        assert "new_agent" in new_state.agent_positions
        assert new_state.agent_positions["new_agent"] == "c"


class TestBatchMoveAdvanced:
    """Advanced tests for move_agents_batch."""

    def test_batch_move_multiple_agents_to_same_location(self, mutable_spatial_state):
        """Can move multiple agents to same location."""
        moves = {"agent_1": "c", "agent_2": "c"}
        new_state = SpatialMutations.move_agents_batch(mutable_spatial_state, moves)
        assert new_state.agent_positions["agent_1"] == "c"
        assert new_state.agent_positions["agent_2"] == "c"

    def test_batch_move_validates_all_before_applying_any(self, mutable_spatial_state):
        """Validates all moves before applying (atomic)."""
        moves = {"agent_1": "b", "agent_2": "invalid"}
        with pytest.raises(ValueError):
            SpatialMutations.move_agents_batch(mutable_spatial_state, moves)
        # Original state unchanged
        assert mutable_spatial_state.agent_positions["agent_1"] == "a"


class TestLocationAttributeMutations:
    """Tests for location attribute mutations."""

    def test_setting_new_attribute_adds_it(self, mutable_spatial_state):
        """Setting new attribute adds it to location."""
        new_state = SpatialMutations.set_location_attribute(mutable_spatial_state, "a", "new_attr", "value")
        assert new_state.locations["a"].attributes["new_attr"] == "value"
        assert new_state.locations["a"].attributes["resource"] == 100  # Existing preserved

    def test_updating_existing_attribute_changes_it(self, mutable_spatial_state):
        """Updating existing attribute changes value."""
        new_state = SpatialMutations.set_location_attribute(mutable_spatial_state, "a", "resource", 200)
        assert new_state.locations["a"].attributes["resource"] == 200

    def test_update_multiple_attributes_merges_correctly(self, mutable_spatial_state):
        """update_location_attributes merges new attributes."""
        updates = {"resource": 150, "terrain": "forest"}
        new_state = SpatialMutations.update_location_attributes(mutable_spatial_state, "a", updates)
        assert new_state.locations["a"].attributes["resource"] == 150
        assert new_state.locations["a"].attributes["terrain"] == "forest"
        assert new_state.locations["a"].attributes["population"] == 1000  # Existing preserved

    def test_update_with_empty_dict_preserves_state(self, mutable_spatial_state):
        """Empty updates dict preserves state."""
        new_state = SpatialMutations.update_location_attributes(mutable_spatial_state, "a", {})
        assert new_state.locations["a"].attributes == mutable_spatial_state.locations["a"].attributes


class TestNetworkMutations:
    """Tests for network mutations."""

    def test_adding_connection_to_existing_network(self, mutable_spatial_state):
        """Adding connection to existing network."""
        new_state = SpatialMutations.add_connection(mutable_spatial_state, "a", "c", network="default")
        assert ("a", "c") in new_state.networks["default"].edges

    def test_adding_connection_with_attributes(self, mutable_spatial_state):
        """Adding connection with attributes creates connection entry."""
        attributes = {"cost": 15, "speed": 3}
        new_state = SpatialMutations.add_connection(
            mutable_spatial_state, "a", "c", network="default", attributes=attributes
        )
        # Should create connection in connections dict
        assert ("a", "c") in new_state.connections or ("c", "a") in new_state.connections

    def test_removing_connection_from_network(self, mutable_spatial_state):
        """Removing connection from network."""
        new_state = SpatialMutations.remove_connection(mutable_spatial_state, "a", "b", network="default")
        assert ("a", "b") not in new_state.networks["default"].edges
        assert ("b", "a") not in new_state.networks["default"].edges

    def test_removing_nonexistent_connection_is_idempotent(self, mutable_spatial_state):
        """Removing non-existent connection doesn't raise."""
        new_state = SpatialMutations.remove_connection(mutable_spatial_state, "a", "c", network="default")
        assert isinstance(new_state, SpatialState)


class TestConnectionAttributeMutations:
    """Tests for connection attribute mutations."""

    def test_updating_connection_attribute(self, mutable_spatial_state):
        """Updating connection attribute changes value."""
        new_state = SpatialMutations.update_connection_attribute(mutable_spatial_state, "a", "b", "cost", 20)
        assert new_state.connections[("a", "b")].attributes["cost"] == 20
        assert new_state.connections[("a", "b")].attributes["speed"] == 5  # Other preserved

    def test_adding_new_connection_attribute(self, mutable_spatial_state):
        """Adding new attribute to connection."""
        new_state = SpatialMutations.update_connection_attribute(mutable_spatial_state, "a", "b", "capacity", 1000)
        assert new_state.connections[("a", "b")].attributes["capacity"] == 1000


class TestNetworkManagement:
    """Tests for network creation/removal."""

    def test_creating_new_network(self, mutable_spatial_state):
        """Creating new network layer."""
        edges = {("a", "b")}
        new_state = SpatialMutations.create_network(mutable_spatial_state, "rail", edges=edges)
        assert "rail" in new_state.networks
        assert new_state.networks["rail"].edges == edges

    def test_creating_network_with_empty_edges(self, mutable_spatial_state):
        """Creating network with no edges."""
        new_state = SpatialMutations.create_network(mutable_spatial_state, "air", edges=None)
        assert "air" in new_state.networks
        assert new_state.networks["air"].edges == set()

    def test_removing_custom_network(self, mutable_spatial_state):
        """Removing custom network layer."""
        state_with_rail = SpatialMutations.create_network(mutable_spatial_state, "rail", edges=set())
        new_state = SpatialMutations.remove_network(state_with_rail, "rail")
        assert "rail" not in new_state.networks

    def test_cannot_remove_default_network(self, mutable_spatial_state):
        """Cannot remove default network."""
        with pytest.raises(ValueError, match="default"):
            SpatialMutations.remove_network(mutable_spatial_state, "default")

    def test_removing_nonexistent_network_is_idempotent(self, mutable_spatial_state):
        """Removing non-existent network doesn't raise."""
        new_state = SpatialMutations.remove_network(mutable_spatial_state, "nonexistent")
        assert isinstance(new_state, SpatialState)


class TestApplyToRegion:
    """Tests for batch regional updates."""

    def test_applies_function_to_multiple_locations(self, mutable_spatial_state):
        """Applies update function to all specified locations."""
        def double_resource(loc: LocationState) -> dict:
            return {"resource": loc.attributes["resource"] * 2}

        new_state = SpatialMutations.apply_to_region(mutable_spatial_state, ["a", "b"], double_resource)
        assert new_state.locations["a"].attributes["resource"] == 200
        assert new_state.locations["b"].attributes["resource"] == 100
        assert new_state.locations["c"].attributes["resource"] == 25  # Unchanged

    def test_apply_with_empty_location_list(self, mutable_spatial_state):
        """Empty location list preserves state."""
        def update(loc: LocationState) -> dict:
            return {"resource": 0}

        new_state = SpatialMutations.apply_to_region(mutable_spatial_state, [], update)
        # All locations unchanged
        assert new_state.locations["a"].attributes["resource"] == 100

    def test_apply_validates_all_locations_first(self, mutable_spatial_state):
        """Validates all locations before applying updates."""
        def update(loc: LocationState) -> dict:
            return {"resource": 0}

        with pytest.raises(ValueError):
            SpatialMutations.apply_to_region(mutable_spatial_state, ["a", "invalid"], update)
        # Original unchanged
        assert mutable_spatial_state.locations["a"].attributes["resource"] == 100


class TestImmutability:
    """Tests verifying immutability guarantees."""

    def test_all_mutations_preserve_input_state(self, mutable_spatial_state):
        """All mutation operations preserve input state."""
        original_agent_pos = dict(mutable_spatial_state.agent_positions)
        original_locations = dict(mutable_spatial_state.locations)

        # Perform various mutations
        SpatialMutations.move_agent(mutable_spatial_state, "agent_1", "b")
        SpatialMutations.set_location_attribute(mutable_spatial_state, "a", "resource", 200)
        SpatialMutations.add_connection(mutable_spatial_state, "a", "c", network="default")

        # Original state unchanged
        assert mutable_spatial_state.agent_positions == original_agent_pos
        assert mutable_spatial_state.locations == original_locations

    def test_nested_mutations_work_correctly(self, mutable_spatial_state):
        """Can chain mutations correctly."""
        state1 = SpatialMutations.move_agent(mutable_spatial_state, "agent_1", "b")
        state2 = SpatialMutations.move_agent(state1, "agent_2", "c")

        assert state2.agent_positions["agent_1"] == "b"
        assert state2.agent_positions["agent_2"] == "c"
        # Original unchanged
        assert mutable_spatial_state.agent_positions["agent_1"] == "a"


class TestErrorMessages:
    """Tests for clear error messages."""

    def test_move_to_invalid_location_has_clear_error(self, mutable_spatial_state):
        """Error message includes valid locations."""
        with pytest.raises(ValueError) as exc_info:
            SpatialMutations.move_agent(mutable_spatial_state, "agent_1", "invalid")
        error_msg = str(exc_info.value)
        # Should mention the invalid location and list valid ones
        assert "invalid" in error_msg.lower()

    def test_invalid_network_has_clear_error(self, mutable_spatial_state):
        """Error message for invalid network."""
        with pytest.raises(ValueError) as exc_info:
            SpatialMutations.add_connection(mutable_spatial_state, "a", "b", network="invalid")
        error_msg = str(exc_info.value)
        assert "network" in error_msg.lower()


class TestEdgeCases:
    """Edge case tests."""

    def test_mutations_on_minimal_state(self):
        """Mutations work on minimal spatial state."""
        state = SpatialState(
            topology_type="grid",
            locations={"0,0": LocationState(id="0,0")},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        new_state = SpatialMutations.move_agent(state, "agent", "0,0")
        assert new_state.agent_positions["agent"] == "0,0"

    def test_large_batch_operations(self):
        """Handles large batch operations efficiently."""
        locations = {f"loc_{i}": LocationState(id=f"loc_{i}") for i in range(100)}
        state = SpatialState(
            topology_type="grid",
            locations=locations,
            networks={"default": NetworkState(name="default", edges=set())}
        )
        # Batch move many agents
        moves = {f"agent_{i}": f"loc_{i % 100}" for i in range(1000)}
        new_state = SpatialMutations.move_agents_batch(state, moves)
        assert len(new_state.agent_positions) == 1000
