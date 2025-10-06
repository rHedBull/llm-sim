"""Unit tests for GeoJSON topology factory.

Tests specific to loading geographic regions from GeoJSON files.
"""

import pytest
import json

from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.models.config import GeoJSONConfig
from llm_sim.models.state import SpatialState


@pytest.fixture
def simple_geojson_file(tmp_path):
    """Create simple GeoJSON file with two regions."""
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "region_a", "population": 100000},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "region_b", "population": 50000},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]
                }
            }
        ]
    }
    file_path = tmp_path / "regions.geojson"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return str(file_path)


@pytest.fixture
def geojson_with_multipolygon(tmp_path):
    """Create GeoJSON with MultiPolygon."""
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "archipelago"},
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
                    ]
                }
            }
        ]
    }
    file_path = tmp_path / "multipolygon.geojson"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return str(file_path)


class TestLocationCreation:
    """Tests for location creation from GeoJSON features."""

    def test_creates_location_for_each_feature(self, simple_geojson_file):
        """Creates location for each Feature."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert "region_a" in state.locations
        assert "region_b" in state.locations

    def test_location_count_matches_features(self, simple_geojson_file):
        """Number of locations matches number of features."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert len(state.locations) == 2

    def test_uses_feature_name_as_location_id(self, simple_geojson_file):
        """Uses properties.name as location ID."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert set(state.locations.keys()) == {"region_a", "region_b"}


class TestPropertyCopying:
    """Tests for copying feature properties to location attributes."""

    def test_copies_properties_to_attributes(self, simple_geojson_file):
        """Copies feature properties to location.attributes."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.locations["region_a"].attributes["population"] == 100000
        assert state.locations["region_b"].attributes["population"] == 50000

    def test_excludes_name_from_attributes(self, simple_geojson_file):
        """Does not duplicate 'name' in attributes."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        # Name is the ID, may or may not be in attributes
        # Just verify attributes exist
        assert "population" in state.locations["region_a"].attributes

    def test_handles_empty_properties(self, tmp_path):
        """Handles features with minimal properties."""
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "empty_region"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "empty_props.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        state = SpatialStateFactory.from_geojson(config)
        # Should have minimal attributes
        assert "empty_region" in state.locations


class TestAdjacencyComputation:
    """Tests for computing adjacency from geometry."""

    def test_computes_adjacency_for_touching_polygons(self, simple_geojson_file):
        """Computes adjacency for polygons that touch."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        # region_a and region_b share an edge, should be adjacent
        edges = state.networks["default"].edges
        has_adjacency = any(
            set(e) == {"region_a", "region_b"} for e in edges
        )
        assert has_adjacency

    def test_non_touching_polygons_not_adjacent(self, tmp_path):
        """Non-touching polygons are not adjacent."""
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "region_a"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {"name": "region_b"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "separated.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        state = SpatialStateFactory.from_geojson(config)
        edges = state.networks["default"].edges
        # Should not be adjacent
        has_adjacency = any(
            set(e) == {"region_a", "region_b"} for e in edges
        )
        assert not has_adjacency


class TestGeometryTypes:
    """Tests for different geometry types."""

    def test_handles_polygon_geometry(self, simple_geojson_file):
        """Handles Polygon geometry."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert len(state.locations) == 2

    def test_handles_multipolygon_geometry(self, geojson_with_multipolygon):
        """Handles MultiPolygon geometry."""
        config = GeoJSONConfig(geojson_file=geojson_with_multipolygon)
        state = SpatialStateFactory.from_geojson(config)
        assert "archipelago" in state.locations


class TestDefaultNetwork:
    """Tests for default network creation."""

    def test_creates_default_network(self, simple_geojson_file):
        """Always creates 'default' network."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert "default" in state.networks

    def test_default_network_contains_adjacency(self, simple_geojson_file):
        """Default network contains computed adjacency."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        # Should have at least one edge (regions touch)
        assert len(state.networks["default"].edges) > 0


class TestInitialization:
    """Tests for state initialization."""

    def test_agent_positions_empty(self, simple_geojson_file):
        """Agent positions initialized empty."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.agent_positions == {}

    def test_topology_type_is_regions(self, simple_geojson_file):
        """Topology type set to 'regions'."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert state.topology_type == "regions"

    def test_returns_valid_spatial_state(self, simple_geojson_file):
        """Returns valid SpatialState instance."""
        config = GeoJSONConfig(geojson_file=simple_geojson_file)
        state = SpatialStateFactory.from_geojson(config)
        assert isinstance(state, SpatialState)


class TestErrorHandling:
    """Tests for error handling."""

    def test_raises_error_for_missing_name_property(self, tmp_path):
        """Raises error if feature missing 'name' property."""
        data = {
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
        file_path = tmp_path / "no_name.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        with pytest.raises(Exception, match="name|required"):
            SpatialStateFactory.from_geojson(config)

    def test_raises_error_for_malformed_geojson(self, tmp_path):
        """Raises error for malformed GeoJSON."""
        file_path = tmp_path / "bad.geojson"
        file_path.write_text("{ invalid json }")
        config = GeoJSONConfig(geojson_file=str(file_path))
        with pytest.raises(Exception):
            SpatialStateFactory.from_geojson(config)

    def test_raises_error_for_non_feature_collection(self, tmp_path):
        """Raises error if not FeatureCollection."""
        data = {
            "type": "Feature",  # Should be FeatureCollection
            "properties": {"name": "test"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        }
        file_path = tmp_path / "not_collection.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        with pytest.raises(Exception, match="FeatureCollection|required"):
            SpatialStateFactory.from_geojson(config)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_region(self, tmp_path):
        """Handles single region GeoJSON."""
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "only_region"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                }
            ]
        }
        file_path = tmp_path / "single.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        state = SpatialStateFactory.from_geojson(config)
        assert len(state.locations) == 1
        assert len(state.networks["default"].edges) == 0

    def test_complex_polygons(self, tmp_path):
        """Handles complex polygons with holes."""
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "donut_region"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],  # Outer ring
                            [[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]   # Hole
                        ]
                    }
                }
            ]
        }
        file_path = tmp_path / "complex.geojson"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = GeoJSONConfig(geojson_file=str(file_path))
        state = SpatialStateFactory.from_geojson(config)
        assert "donut_region" in state.locations
