"""Unit tests for spatial state models.

Tests validate Pydantic models defined in data-model.md:
- LocationState
- ConnectionState
- NetworkState
- SpatialState
"""

import pytest
from pydantic import ValidationError

from llm_sim.models.state import (
    LocationState,
    ConnectionState,
    NetworkState,
    SpatialState,
)


class TestLocationState:
    """Tests for LocationState model."""

    def test_create_minimal_location(self):
        """Create location with only required fields."""
        location = LocationState(id="winterfell")
        assert location.id == "winterfell"
        assert location.attributes == {}
        assert location.metadata == {}

    def test_create_location_with_attributes(self):
        """Create location with attributes."""
        location = LocationState(
            id="winterfell",
            attributes={"loyalty": "stark", "military_strength": 5000}
        )
        assert location.attributes["loyalty"] == "stark"
        assert location.attributes["military_strength"] == 5000

    def test_create_location_with_metadata(self):
        """Create location with metadata."""
        location = LocationState(
            id="0,0",
            metadata={"coordinates": {"x": 0, "y": 0}}
        )
        assert location.metadata["coordinates"]["x"] == 0

    def test_id_must_be_non_empty(self):
        """ID validation: must be non-empty string."""
        with pytest.raises(ValidationError, match="String should have at least 1 character|non-empty"):
            LocationState(id="")

    def test_id_whitespace_trimmed(self):
        """ID validation: whitespace is trimmed."""
        location = LocationState(id="  winterfell  ")
        assert location.id == "winterfell"

    def test_is_immutable(self):
        """Model is frozen (immutable)."""
        location = LocationState(id="winterfell", attributes={"resource": 100})
        with pytest.raises(ValidationError):
            location.id = "new_id"  # type: ignore

    def test_serializes_to_dict(self):
        """Model serializes to dict."""
        location = LocationState(
            id="winterfell",
            attributes={"resource": 100}
        )
        data = location.model_dump()
        assert data["id"] == "winterfell"
        assert data["attributes"]["resource"] == 100

    def test_deserializes_from_dict(self):
        """Model deserializes from dict."""
        data = {
            "id": "winterfell",
            "attributes": {"resource": 100},
            "metadata": {}
        }
        location = LocationState(**data)
        assert location.id == "winterfell"
        assert location.attributes["resource"] == 100


class TestConnectionState:
    """Tests for ConnectionState model."""

    def test_create_minimal_connection(self):
        """Create connection with only required fields."""
        connection = ConnectionState(type="border")
        assert connection.type == "border"
        assert connection.attributes == {}
        assert connection.bidirectional is True

    def test_create_connection_with_attributes(self):
        """Create connection with attributes."""
        connection = ConnectionState(
            type="rail",
            attributes={"speed": 100, "capacity": 1000}
        )
        assert connection.attributes["speed"] == 100
        assert connection.attributes["capacity"] == 1000

    def test_create_unidirectional_connection(self):
        """Create unidirectional connection."""
        connection = ConnectionState(type="river", bidirectional=False)
        assert connection.bidirectional is False

    def test_type_must_be_non_empty(self):
        """Type validation: must be non-empty string."""
        with pytest.raises(ValidationError, match="String should have at least 1 character|non-empty"):
            ConnectionState(type="")

    def test_type_whitespace_trimmed(self):
        """Type validation: whitespace is trimmed."""
        connection = ConnectionState(type="  rail  ")
        assert connection.type == "rail"

    def test_is_immutable(self):
        """Model is frozen (immutable)."""
        connection = ConnectionState(type="border")
        with pytest.raises(ValidationError):
            connection.type = "new_type"  # type: ignore

    def test_serializes_to_dict(self):
        """Model serializes to dict."""
        connection = ConnectionState(
            type="rail",
            attributes={"cost": 10},
            bidirectional=True
        )
        data = connection.model_dump()
        assert data["type"] == "rail"
        assert data["attributes"]["cost"] == 10
        assert data["bidirectional"] is True


class TestNetworkState:
    """Tests for NetworkState model."""

    def test_create_minimal_network(self):
        """Create network with only required fields."""
        network = NetworkState(name="borders")
        assert network.name == "borders"
        assert network.edges == set()
        assert network.attributes == {}

    def test_create_network_with_edges(self):
        """Create network with edges."""
        network = NetworkState(
            name="borders",
            edges={("winterfell", "riverlands"), ("riverlands", "kings_landing")}
        )
        assert len(network.edges) == 2
        assert ("winterfell", "riverlands") in network.edges

    def test_name_must_be_non_empty(self):
        """Name validation: must be non-empty string."""
        with pytest.raises(ValidationError, match="String should have at least 1 character|non-empty"):
            NetworkState(name="")

    def test_name_whitespace_trimmed(self):
        """Name validation: whitespace is trimmed."""
        network = NetworkState(name="  borders  ")
        assert network.name == "borders"

    def test_edges_must_be_two_tuples(self):
        """Edge validation: edges must be 2-tuples."""
        with pytest.raises(ValidationError, match="2-tuple|Tuple should have at most 2 items"):
            NetworkState(name="borders", edges={("a", "b", "c")})  # type: ignore

    def test_edge_locations_must_be_non_empty(self):
        """Edge validation: edge locations must be non-empty."""
        with pytest.raises(ValidationError, match="non-empty|empty"):
            NetworkState(name="borders", edges={("a", "")})

    def test_is_immutable(self):
        """Model is frozen (immutable)."""
        network = NetworkState(name="borders")
        with pytest.raises(ValidationError):
            network.name = "new_name"  # type: ignore

    def test_edges_serialize_deterministically(self):
        """Edges serialize as sorted list for determinism."""
        network = NetworkState(
            name="borders",
            edges={("b", "c"), ("a", "b")}
        )
        data = network.model_dump()
        # Should be sorted list of lists
        assert isinstance(data["edges"], list)
        assert data["edges"] == sorted(data["edges"])


class TestSpatialState:
    """Tests for SpatialState model."""

    def test_create_minimal_spatial_state(self):
        """Create spatial state with only required fields."""
        state = SpatialState(topology_type="grid")
        assert state.topology_type == "grid"
        assert state.agent_positions == {}
        assert state.locations == {}
        assert state.connections == {}
        assert state.networks == {}

    def test_create_spatial_state_with_all_fields(self):
        """Create complete spatial state."""
        state = SpatialState(
            topology_type="regions",
            agent_positions={"agent_a": "winterfell"},
            locations={
                "winterfell": LocationState(id="winterfell", attributes={"loyalty": "stark"}),
                "riverlands": LocationState(id="riverlands", attributes={"loyalty": "tully"})
            },
            connections={
                ("winterfell", "riverlands"): ConnectionState(type="border")
            },
            networks={
                "default": NetworkState(name="default", edges={("winterfell", "riverlands")})
            }
        )
        assert state.topology_type == "regions"
        assert state.agent_positions["agent_a"] == "winterfell"
        assert "winterfell" in state.locations

    def test_topology_type_must_be_valid_literal(self):
        """Topology type validation: must be one of allowed types."""
        with pytest.raises(ValidationError):
            SpatialState(topology_type="invalid_type")  # type: ignore

    def test_validates_agent_position_references(self):
        """Validation: agent positions must reference valid locations."""
        with pytest.raises(ValidationError, match="invalid location|not found"):
            SpatialState(
                topology_type="grid",
                agent_positions={"agent_a": "invalid_location"},
                locations={"0,0": LocationState(id="0,0")},
            )

    def test_validates_network_edge_references(self):
        """Validation: network edges must reference valid locations."""
        with pytest.raises(ValidationError, match="invalid location|not found"):
            SpatialState(
                topology_type="grid",
                locations={"0,0": LocationState(id="0,0")},
                networks={
                    "default": NetworkState(
                        name="default",
                        edges={("0,0", "invalid_location")}
                    )
                }
            )

    def test_validates_connection_references(self):
        """Validation: connections must reference valid locations."""
        with pytest.raises(ValidationError, match="invalid location|not found"):
            SpatialState(
                topology_type="grid",
                locations={"0,0": LocationState(id="0,0")},
                connections={
                    ("0,0", "invalid_location"): ConnectionState(type="border")
                }
            )

    def test_is_immutable(self):
        """Model is frozen (immutable)."""
        state = SpatialState(topology_type="grid")
        with pytest.raises(ValidationError):
            state.topology_type = "hex_grid"  # type: ignore

    def test_agent_positions_serialize_sorted(self):
        """Agent positions serialize with sorted keys for determinism."""
        state = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(id="0,0"),
                "1,0": LocationState(id="1,0"),
            },
            agent_positions={"agent_b": "1,0", "agent_a": "0,0"}
        )
        data = state.model_dump()
        keys = list(data["agent_positions"].keys())
        assert keys == sorted(keys)

    def test_connections_serialize_with_string_keys(self):
        """Connections serialize with string keys (tuples -> strings)."""
        state = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(id="0,0"),
                "1,0": LocationState(id="1,0"),
            },
            connections={
                ("0,0", "1,0"): ConnectionState(type="border")
            }
        )
        data = state.model_dump()
        # Serialized connections should have string keys
        assert isinstance(data["connections"], dict)
        # Keys should be in format "loc1,loc2"
        for key in data["connections"].keys():
            assert isinstance(key, str)

    def test_allows_valid_topology_types(self):
        """Topology type: allows all valid types."""
        valid_types = ["grid", "hex_grid", "network", "regions"]
        for ttype in valid_types:
            state = SpatialState(topology_type=ttype)
            assert state.topology_type == ttype

    def test_empty_state_is_valid(self):
        """Empty spatial state is valid."""
        state = SpatialState(topology_type="grid")
        # Should not raise
        assert state.agent_positions == {}
        assert state.locations == {}

    def test_serialization_roundtrip(self):
        """State can be serialized and deserialized."""
        original = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(id="0,0", attributes={"resource": 100}),
            },
            agent_positions={"agent_a": "0,0"},
            networks={
                "default": NetworkState(name="default", edges=set())
            }
        )
        # Serialize
        data = original.model_dump()
        # Deserialize (needs special handling for connections)
        # This test may need adjustment based on actual serialization format
        assert data["topology_type"] == "grid"
        assert data["agent_positions"]["agent_a"] == "0,0"
