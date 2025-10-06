"""Unit tests for spatial state serialization/deserialization.

Tests JSON serialization, checkpoint persistence, and roundtrip conversion.
"""

import pytest
import json

from llm_sim.models.state import (
    SpatialState,
    LocationState,
    ConnectionState,
    NetworkState,
)


@pytest.fixture
def complete_spatial_state():
    """Create complete spatial state with all fields."""
    return SpatialState(
        topology_type="regions",
        agent_positions={
            "agent_a": "winterfell",
            "agent_b": "kings_landing",
        },
        locations={
            "winterfell": LocationState(
                id="winterfell",
                attributes={"loyalty": "stark", "military": 5000},
                metadata={"region": "north"}
            ),
            "kings_landing": LocationState(
                id="kings_landing",
                attributes={"loyalty": "baratheon", "military": 10000},
                metadata={"region": "crownlands"}
            ),
        },
        connections={
            ("winterfell", "kings_landing"): ConnectionState(
                type="road",
                attributes={"distance": 1000, "travel_days": 30},
                bidirectional=True
            ),
        },
        networks={
            "default": NetworkState(
                name="default",
                edges={("winterfell", "kings_landing")},
                attributes={"type": "land_routes"}
            ),
        }
    )


class TestSpatialStateSerialization:
    """Tests for SpatialState serialization."""

    def test_serializes_to_dict(self, complete_spatial_state):
        """SpatialState serializes to dictionary."""
        data = complete_spatial_state.model_dump()
        assert isinstance(data, dict)
        assert data["topology_type"] == "regions"

    def test_agent_positions_serialized_sorted(self, complete_spatial_state):
        """Agent positions serialized with sorted keys."""
        data = complete_spatial_state.model_dump()
        keys = list(data["agent_positions"].keys())
        assert keys == sorted(keys)

    def test_locations_serialized(self, complete_spatial_state):
        """Locations serialized correctly."""
        data = complete_spatial_state.model_dump()
        assert "winterfell" in data["locations"]
        assert data["locations"]["winterfell"]["id"] == "winterfell"
        assert data["locations"]["winterfell"]["attributes"]["loyalty"] == "stark"

    def test_connections_serialized_with_string_keys(self, complete_spatial_state):
        """Connections serialized with string keys (not tuples)."""
        data = complete_spatial_state.model_dump()
        # Keys should be strings like "loc1,loc2"
        assert isinstance(data["connections"], dict)
        for key in data["connections"].keys():
            assert isinstance(key, str)
            assert "," in key  # Should contain comma separator

    def test_networks_serialized(self, complete_spatial_state):
        """Networks serialized correctly."""
        data = complete_spatial_state.model_dump()
        assert "default" in data["networks"]
        assert data["networks"]["default"]["name"] == "default"

    def test_network_edges_serialized_as_sorted_list(self, complete_spatial_state):
        """Network edges serialized as sorted list."""
        data = complete_spatial_state.model_dump()
        edges = data["networks"]["default"]["edges"]
        assert isinstance(edges, list)
        # Should be sorted
        assert edges == sorted(edges)


class TestSpatialStateDeserialization:
    """Tests for SpatialState deserialization."""

    def test_deserializes_from_dict(self, complete_spatial_state):
        """SpatialState deserializes from dictionary."""
        data = complete_spatial_state.model_dump()
        # Note: Connections need special handling for tuple keys
        # This test may need adjustment based on actual deserialization
        restored = SpatialState(**data)
        assert restored.topology_type == "regions"

    def test_locations_deserialized(self, complete_spatial_state):
        """Locations deserialized correctly."""
        data = complete_spatial_state.model_dump()
        restored = SpatialState(**data)
        assert "winterfell" in restored.locations
        assert isinstance(restored.locations["winterfell"], LocationState)
        assert restored.locations["winterfell"].attributes["loyalty"] == "stark"

    def test_agent_positions_deserialized(self, complete_spatial_state):
        """Agent positions deserialized correctly."""
        data = complete_spatial_state.model_dump()
        restored = SpatialState(**data)
        assert restored.agent_positions["agent_a"] == "winterfell"


class TestRoundtripSerialization:
    """Tests for serialization roundtrip."""

    def test_minimal_state_roundtrip(self):
        """Minimal spatial state roundtrip."""
        original = SpatialState(
            topology_type="grid",
            locations={"0,0": LocationState(id="0,0")},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        data = original.model_dump()
        restored = SpatialState(**data)
        assert restored.topology_type == original.topology_type
        assert "0,0" in restored.locations

    def test_complete_state_roundtrip(self, complete_spatial_state):
        """Complete spatial state roundtrip."""
        data = complete_spatial_state.model_dump()
        restored = SpatialState(**data)

        # Verify key fields preserved
        assert restored.topology_type == complete_spatial_state.topology_type
        assert restored.agent_positions == complete_spatial_state.agent_positions
        assert set(restored.locations.keys()) == set(complete_spatial_state.locations.keys())


class TestJSONSerialization:
    """Tests for JSON string serialization."""

    def test_serializes_to_json_string(self, complete_spatial_state):
        """SpatialState serializes to JSON string."""
        json_str = complete_spatial_state.model_dump_json()
        assert isinstance(json_str, str)
        # Should be valid JSON
        data = json.loads(json_str)
        assert data["topology_type"] == "regions"

    def test_json_is_valid_and_parseable(self, complete_spatial_state):
        """Serialized JSON is valid and parseable."""
        json_str = complete_spatial_state.model_dump_json()
        data = json.loads(json_str)
        # Should be a dict with expected keys
        assert "topology_type" in data
        assert "locations" in data
        assert "agent_positions" in data

    def test_deserializes_from_json_string(self, complete_spatial_state):
        """SpatialState deserializes from JSON string."""
        json_str = complete_spatial_state.model_dump_json()
        restored = SpatialState.model_validate_json(json_str)
        assert restored.topology_type == complete_spatial_state.topology_type


class TestCheckpointIntegration:
    """Tests for checkpoint file integration."""

    def test_spatial_state_in_simulation_state_checkpoint(self, complete_spatial_state, mock_global_state):
        """SpatialState serializes as part of SimulationState checkpoint."""
        from llm_sim.models.state import SimulationState

        state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=complete_spatial_state
        )

        # Serialize entire simulation state
        data = state.model_dump()
        assert "spatial_state" in data
        assert data["spatial_state"]["topology_type"] == "regions"

    def test_none_spatial_state_serializes_correctly(self, mock_global_state):
        """None spatial_state serializes as null."""
        from llm_sim.models.state import SimulationState

        state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )

        data = state.model_dump()
        assert data["spatial_state"] is None


class TestSerializationEdgeCases:
    """Tests for edge cases in serialization."""

    def test_empty_agent_positions(self):
        """Empty agent_positions serializes correctly."""
        state = SpatialState(
            topology_type="grid",
            agent_positions={},
            locations={"0,0": LocationState(id="0,0")},
            networks={"default": NetworkState(name="default", edges=set())}
        )
        data = state.model_dump()
        assert data["agent_positions"] == {}

    def test_empty_networks(self):
        """Empty networks dict serializes correctly."""
        state = SpatialState(
            topology_type="grid",
            locations={"0,0": LocationState(id="0,0")},
            networks={}
        )
        data = state.model_dump()
        assert data["networks"] == {}

    def test_complex_nested_attributes(self):
        """Complex nested attributes serialize correctly."""
        state = SpatialState(
            topology_type="grid",
            locations={
                "0,0": LocationState(
                    id="0,0",
                    attributes={
                        "nested": {
                            "level1": {
                                "level2": [1, 2, 3],
                                "data": {"key": "value"}
                            }
                        }
                    }
                )
            },
            networks={"default": NetworkState(name="default", edges=set())}
        )
        data = state.model_dump()
        assert data["locations"]["0,0"]["attributes"]["nested"]["level1"]["level2"] == [1, 2, 3]

    def test_unicode_in_location_ids(self):
        """Unicode characters in location IDs serialize correctly."""
        state = SpatialState(
            topology_type="regions",
            locations={
                "北京": LocationState(id="北京", attributes={"name": "Beijing"}),
                "東京": LocationState(id="東京", attributes={"name": "Tokyo"}),
            },
            networks={"default": NetworkState(name="default", edges=set())}
        )
        json_str = state.model_dump_json()
        restored = SpatialState.model_validate_json(json_str)
        assert "北京" in restored.locations
        assert "東京" in restored.locations


class TestSerializationPerformance:
    """Performance tests for serialization."""

    def test_large_state_serialization(self):
        """Large spatial state serializes efficiently."""
        locations = {f"loc_{i}": LocationState(id=f"loc_{i}") for i in range(1000)}
        agent_positions = {f"agent_{i}": f"loc_{i % 1000}" for i in range(10000)}
        state = SpatialState(
            topology_type="grid",
            locations=locations,
            agent_positions=agent_positions,
            networks={"default": NetworkState(name="default", edges=set())}
        )

        # Should complete quickly
        data = state.model_dump()
        assert len(data["locations"]) == 1000
        assert len(data["agent_positions"]) == 10000

    def test_large_network_serialization(self):
        """Large network edges serialize efficiently."""
        locations = {f"loc_{i}": LocationState(id=f"loc_{i}") for i in range(100)}
        edges = {(f"loc_{i}", f"loc_{i+1}") for i in range(99)}
        state = SpatialState(
            topology_type="network",
            locations=locations,
            networks={
                "default": NetworkState(name="default", edges=edges)
            }
        )

        # Should complete quickly
        json_str = state.model_dump_json()
        assert len(json_str) > 0
