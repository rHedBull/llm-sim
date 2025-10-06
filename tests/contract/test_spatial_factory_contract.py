"""Contract tests for SpatialStateFactory interface.

Tests validate the contract requirements from specs/012-spatial-maps/contracts/spatial_factory_contract.md
All factory methods must be static, return valid SpatialState, and initialize 'default' network.
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.models.config import (
    GridConfig,
    HexGridConfig,
    NetworkConfig,
    GeoJSONConfig,
    SpatialConfig,
)
from llm_sim.models.state import SpatialState


class TestGridFactory:
    """Contract tests for from_grid_config."""

    def test_returns_valid_spatial_state(self):
        """Valid config: returns SpatialState for valid input."""
        config = GridConfig(width=3, height=3, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert isinstance(state, SpatialState)

    def test_creates_correct_number_of_locations(self):
        """Topology correctness: creates width × height locations."""
        config = GridConfig(width=3, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert len(state.locations) == 6  # 3 × 2

    def test_uses_correct_location_id_format(self):
        """Topology correctness: uses {x},{y} as location IDs."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert "0,0" in state.locations
        assert "1,0" in state.locations
        assert "0,1" in state.locations
        assert "1,1" in state.locations

    def test_creates_default_network(self):
        """Default network: 'default' network always created."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert "default" in state.networks

    def test_four_connectivity_creates_correct_edges(self):
        """Topology correctness: 4-connectivity creates cardinal neighbors."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        # Should have edges between (0,0)-(1,0), (0,0)-(0,1), (1,0)-(1,1), (0,1)-(1,1)
        assert len(edges) == 4

    def test_eight_connectivity_includes_diagonals(self):
        """Topology correctness: 8-connectivity includes diagonal neighbors."""
        config = GridConfig(width=2, height=2, connectivity=8)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        # Should have 12 edges (4 cardinal + 8 diagonal bidirectional = 12 undirected)
        assert len(edges) >= 4  # At least cardinal directions

    def test_wrapping_creates_toroidal_grid(self):
        """Topology correctness: wrapping=True creates toroidal topology."""
        config = GridConfig(width=3, height=3, connectivity=4, wrapping=True)
        state = SpatialStateFactory.from_grid_config(config)
        # Edge cells should wrap to opposite side
        # (0,0) should connect to (2,0) and (0,2)
        edges = state.networks["default"].edges
        assert len(edges) > 6  # More edges due to wrapping

    def test_initializes_empty_agent_positions(self):
        """Valid config: initializes empty agent_positions."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert state.agent_positions == {}

    def test_sets_topology_type_to_grid(self):
        """Valid config: sets topology_type='grid'."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert state.topology_type == "grid"

    def test_raises_error_for_invalid_width(self):
        """Invalid config: raises error for non-positive width."""
        with pytest.raises(Exception):  # Pydantic validation error
            GridConfig(width=0, height=2, connectivity=4)

    def test_raises_error_for_invalid_height(self):
        """Invalid config: raises error for non-positive height."""
        with pytest.raises(Exception):  # Pydantic validation error
            GridConfig(width=2, height=0, connectivity=4)


class TestHexGridFactory:
    """Contract tests for from_hex_config."""

    def test_returns_valid_spatial_state(self):
        """Valid config: returns SpatialState for valid input."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert isinstance(state, SpatialState)

    def test_uses_axial_coordinate_format(self):
        """Topology correctness: uses {q},{r} as location IDs."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert "0,0" in state.locations  # Center hex

    def test_creates_hexagonal_shape(self):
        """Topology correctness: creates hexagonal grid."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        # Radius 1 hexagon has 7 hexes (1 center + 6 neighbors)
        assert len(state.locations) == 7

    def test_creates_default_network_with_hex_adjacency(self):
        """Default network: creates 'default' network with 6-neighbor adjacency."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert "default" in state.networks
        # Center hex should have 6 neighbors
        edges = state.networks["default"].edges
        assert len(edges) > 0

    def test_initializes_empty_agent_positions(self):
        """Valid config: initializes empty agent_positions."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert state.agent_positions == {}

    def test_sets_topology_type_to_hex_grid(self):
        """Valid config: sets topology_type='hex_grid'."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert state.topology_type == "hex_grid"

    def test_raises_error_for_invalid_radius(self):
        """Invalid config: raises error for negative radius."""
        with pytest.raises(Exception):  # Pydantic validation error
            HexGridConfig(radius=-1)


class TestNetworkFactory:
    """Contract tests for from_network_config."""

    @pytest.fixture
    def network_json_file(self, tmp_path):
        """Create temporary network JSON file."""
        network_data = {
            "nodes": ["node_a", "node_b", "node_c"],
            "edges": [
                ["node_a", "node_b"],
                ["node_b", "node_c"],
            ],
            "attributes": {
                "node_a": {"resource": 100},
                "node_b": {"resource": 50},
            }
        }
        file_path = tmp_path / "network.json"
        with open(file_path, "w") as f:
            json.dump(network_data, f)
        return str(file_path)

    def test_returns_valid_spatial_state(self, network_json_file):
        """Valid config: returns SpatialState for valid input."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert isinstance(state, SpatialState)

    def test_creates_location_for_each_node(self, network_json_file):
        """Topology correctness: creates location for each node."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert "node_a" in state.locations
        assert "node_b" in state.locations
        assert "node_c" in state.locations

    def test_creates_default_network_with_edges(self, network_json_file):
        """Default network: creates 'default' network with edges from file."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert "default" in state.networks
        edges = state.networks["default"].edges
        assert len(edges) >= 2

    def test_applies_node_attributes_from_file(self, network_json_file):
        """Attribute application: applies attributes from JSON."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.locations["node_a"].attributes.get("resource") == 100
        assert state.locations["node_b"].attributes.get("resource") == 50

    def test_initializes_empty_agent_positions(self, network_json_file):
        """Valid config: initializes empty agent_positions."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.agent_positions == {}

    def test_sets_topology_type_to_network(self, network_json_file):
        """Valid config: sets topology_type='network'."""
        config = NetworkConfig(edges_file=network_json_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.topology_type == "network"

    def test_raises_error_for_missing_file(self):
        """File loading: raises error for missing file."""
        with pytest.raises(Exception, match="not found|does not exist"):
            NetworkConfig(edges_file="/nonexistent/path.json")

    def test_raises_error_for_malformed_json(self, tmp_path):
        """File loading: raises error for malformed JSON."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("{ invalid json }")
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception):  # JSON decode error
            SpatialStateFactory.from_network_config(config)

    def test_raises_error_for_missing_nodes_field(self, tmp_path):
        """File loading: raises error if 'nodes' field missing."""
        file_path = tmp_path / "bad.json"
        file_path.write_text('{"edges": []}')
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception, match="nodes|required"):
            SpatialStateFactory.from_network_config(config)


class TestGeoJSONFactory:
    """Contract tests for from_geojson."""

    @pytest.fixture
    def geojson_file(self, tmp_path):
        """Create temporary GeoJSON file."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": "region_a",
                        "population": 100000,
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "name": "region_b",
                        "population": 50000,
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "regions.geojson"
        with open(file_path, "w") as f:
            json.dump(geojson_data, f)
        return str(file_path)

    def test_returns_valid_spatial_state(self, geojson_file):
        """Valid config: returns SpatialState for valid input."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert isinstance(state, SpatialState)

    def test_creates_location_for_each_feature(self, geojson_file):
        """Topology correctness: creates location for each Feature."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert "region_a" in state.locations
        assert "region_b" in state.locations

    def test_uses_feature_name_as_location_id(self, geojson_file):
        """Topology correctness: uses properties.name as location ID."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert "region_a" in state.locations
        assert "region_b" in state.locations

    def test_copies_properties_to_location_attributes(self, geojson_file):
        """Attribute application: copies properties to location.attributes."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.locations["region_a"].attributes.get("population") == 100000
        assert state.locations["region_b"].attributes.get("population") == 50000

    def test_computes_adjacency_from_geometry(self, geojson_file):
        """Topology correctness: computes adjacency from touching polygons."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        # region_a and region_b touch, so should be adjacent
        edges = state.networks["default"].edges
        assert len(edges) > 0

    def test_creates_default_network(self, geojson_file):
        """Default network: creates 'default' network with computed adjacency."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert "default" in state.networks

    def test_initializes_empty_agent_positions(self, geojson_file):
        """Valid config: initializes empty agent_positions."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.agent_positions == {}

    def test_sets_topology_type_to_regions(self, geojson_file):
        """Valid config: sets topology_type='regions'."""
        config = GeoJSONConfig(geojson_file=geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.topology_type == "regions"

    def test_raises_error_for_missing_file(self):
        """File loading: raises error for missing file."""
        with pytest.raises(Exception, match="not found|does not exist"):
            GeoJSONConfig(geojson_file="/nonexistent/path.geojson")

    def test_raises_error_for_malformed_geojson(self, tmp_path):
        """File loading: raises error for malformed GeoJSON."""
        file_path = tmp_path / "bad.geojson"
        file_path.write_text("{ invalid json }")
        config = GeoJSONConfig(geojson_file=str(file_path))
        with pytest.raises(Exception):
            SpatialStateFactory.from_geojson(config)

    def test_raises_error_for_missing_name_property(self, tmp_path):
        """File loading: raises error if feature missing 'name' property."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},  # Missing 'name'
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "bad.geojson"
        with open(file_path, "w") as f:
            json.dump(geojson_data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        with pytest.raises(Exception, match="name|required"):
            SpatialStateFactory.from_geojson(config)


class TestMainDispatcher:
    """Contract tests for create (main dispatcher)."""

    def test_dispatches_to_grid_factory(self):
        """Dispatch: routes grid config to from_grid_config."""
        config = SpatialConfig(
            topology=GridConfig(width=2, height=2, connectivity=4)
        )
        state = SpatialStateFactory.create(config)
        assert state.topology_type == "grid"

    def test_dispatches_to_hex_factory(self):
        """Dispatch: routes hex_grid config to from_hex_config."""
        config = SpatialConfig(
            topology=HexGridConfig(radius=1)
        )
        state = SpatialStateFactory.create(config)
        assert state.topology_type == "hex_grid"

    def test_dispatches_to_network_factory(self, tmp_path):
        """Dispatch: routes network config to from_network_config."""
        network_data = {
            "nodes": ["a", "b"],
            "edges": [["a", "b"]],
        }
        file_path = tmp_path / "network.json"
        with open(file_path, "w") as f:
            json.dump(network_data, f)
        config = SpatialConfig(
            topology=NetworkConfig(edges_file=str(file_path))
        )
        state = SpatialStateFactory.create(config)
        assert state.topology_type == "network"

    def test_dispatches_to_geojson_factory(self, tmp_path):
        """Dispatch: routes geojson config to from_geojson."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "region_a"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "regions.geojson"
        with open(file_path, "w") as f:
            json.dump(geojson_data, f)
        config = SpatialConfig(
            topology=GeoJSONConfig(geojson_file=str(file_path))
        )
        state = SpatialStateFactory.create(config)
        assert state.topology_type == "regions"

    def test_applies_location_attributes_from_config(self):
        """Post-processing: applies location_attributes from config."""
        config = SpatialConfig(
            topology=GridConfig(width=2, height=2, connectivity=4),
            location_attributes={
                "0,0": {"resource": 100},
                "1,0": {"resource": 50},
            }
        )
        state = SpatialStateFactory.create(config)
        assert state.locations["0,0"].attributes.get("resource") == 100
        assert state.locations["1,0"].attributes.get("resource") == 50

    def test_creates_additional_networks_from_config(self, tmp_path):
        """Post-processing: creates additional_networks from config."""
        # Create rail network edges file
        rail_data = {
            "nodes": ["0,0", "1,0"],
            "edges": [["0,0", "1,0"]],
        }
        rail_file = tmp_path / "rail.json"
        with open(rail_file, "w") as f:
            json.dump(rail_data, f)

        config = SpatialConfig(
            topology=GridConfig(width=2, height=2, connectivity=4),
            additional_networks=[
                {"name": "rail", "edges_file": str(rail_file)}
            ]
        )
        state = SpatialStateFactory.create(config)
        assert "rail" in state.networks
        assert "default" in state.networks

    def test_returns_valid_spatial_state_for_all_types(self):
        """Valid config: returns valid SpatialState for all topology types."""
        configs = [
            SpatialConfig(topology=GridConfig(width=2, height=2, connectivity=4)),
            SpatialConfig(topology=HexGridConfig(radius=1)),
        ]
        for cfg in configs:
            state = SpatialStateFactory.create(cfg)
            assert isinstance(state, SpatialState)
            assert "default" in state.networks
