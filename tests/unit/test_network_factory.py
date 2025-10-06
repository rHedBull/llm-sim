"""Unit tests for network/graph topology factory.

Tests specific to loading arbitrary graphs from JSON edge lists.
"""

import pytest
import json

from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.models.config import NetworkConfig
from llm_sim.models.state import SpatialState


@pytest.fixture
def simple_network_file(tmp_path):
    """Create simple network JSON file."""
    data = {
        "nodes": ["a", "b", "c"],
        "edges": [
            ["a", "b"],
            ["b", "c"],
        ]
    }
    file_path = tmp_path / "network.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return str(file_path)


@pytest.fixture
def network_with_attributes_file(tmp_path):
    """Create network with node attributes."""
    data = {
        "nodes": ["a", "b", "c"],
        "edges": [["a", "b"], ["b", "c"]],
        "attributes": {
            "a": {"resource": 100, "terrain": "plains"},
            "b": {"resource": 50, "terrain": "forest"},
        }
    }
    file_path = tmp_path / "network_attrs.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return str(file_path)


class TestNodeCreation:
    """Tests for node/location creation from JSON."""

    def test_creates_location_for_each_node(self, simple_network_file):
        """Creates location for each node in JSON."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert "a" in state.locations
        assert "b" in state.locations
        assert "c" in state.locations

    def test_node_count_matches_json(self, simple_network_file):
        """Number of locations matches number of nodes."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert len(state.locations) == 3

    def test_uses_node_names_as_location_ids(self, simple_network_file):
        """Uses node names as location IDs."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert set(state.locations.keys()) == {"a", "b", "c"}


class TestEdgeCreation:
    """Tests for edge creation from JSON."""

    def test_creates_edges_from_json(self, simple_network_file):
        """Creates edges in default network from JSON."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        edges = state.networks["default"].edges
        assert len(edges) >= 2

    def test_edge_count_matches_json(self, simple_network_file):
        """Number of edges matches JSON."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        edges = state.networks["default"].edges
        # Should have edges for a-b and b-c
        assert len(edges) == 2

    def test_bidirectional_edges(self, simple_network_file):
        """Edges are bidirectional by default."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        edges = state.networks["default"].edges
        # Check edge exists (either direction)
        has_ab = any(set(e) == {"a", "b"} for e in edges)
        assert has_ab


class TestAttributeApplication:
    """Tests for applying node attributes from JSON."""

    def test_applies_node_attributes_from_json(self, network_with_attributes_file):
        """Applies attributes from JSON to locations."""
        config = NetworkConfig(edges_file=network_with_attributes_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.locations["a"].attributes["resource"] == 100
        assert state.locations["a"].attributes["terrain"] == "plains"

    def test_nodes_without_attributes_have_empty_dict(self, network_with_attributes_file):
        """Nodes without attributes have empty attributes dict."""
        config = NetworkConfig(edges_file=network_with_attributes_file)
        state = SpatialStateFactory.from_network_config(config)
        # Node "c" has no attributes in JSON
        assert state.locations["c"].attributes == {}


class TestDefaultNetwork:
    """Tests for default network creation."""

    def test_creates_default_network(self, simple_network_file):
        """Always creates 'default' network."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert "default" in state.networks

    def test_default_network_contains_all_edges(self, simple_network_file):
        """Default network contains all edges from JSON."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert len(state.networks["default"].edges) > 0


class TestInitialization:
    """Tests for state initialization."""

    def test_agent_positions_empty(self, simple_network_file):
        """Agent positions initialized empty."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.agent_positions == {}

    def test_topology_type_is_network(self, simple_network_file):
        """Topology type set to 'network'."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert state.topology_type == "network"

    def test_returns_valid_spatial_state(self, simple_network_file):
        """Returns valid SpatialState instance."""
        config = NetworkConfig(edges_file=simple_network_file)
        state = SpatialStateFactory.from_network_config(config)
        assert isinstance(state, SpatialState)


class TestErrorHandling:
    """Tests for error handling."""

    def test_raises_error_for_missing_nodes_field(self, tmp_path):
        """Raises error if 'nodes' field missing."""
        file_path = tmp_path / "bad.json"
        file_path.write_text('{"edges": []}')
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception, match="nodes|required"):
            SpatialStateFactory.from_network_config(config)

    def test_raises_error_for_missing_edges_field(self, tmp_path):
        """Raises error if 'edges' field missing."""
        file_path = tmp_path / "bad.json"
        file_path.write_text('{"nodes": []}')
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception, match="edges|required"):
            SpatialStateFactory.from_network_config(config)

    def test_raises_error_for_malformed_json(self, tmp_path):
        """Raises error for malformed JSON."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("{ invalid json }")
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception):
            SpatialStateFactory.from_network_config(config)

    def test_raises_error_for_invalid_edge_reference(self, tmp_path):
        """Raises error if edge references non-existent node."""
        data = {
            "nodes": ["a", "b"],
            "edges": [["a", "nonexistent"]],
        }
        file_path = tmp_path / "bad.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = NetworkConfig(edges_file=str(file_path))
        with pytest.raises(Exception, match="unknown|invalid|not found"):
            SpatialStateFactory.from_network_config(config)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_network(self, tmp_path):
        """Handles network with no edges."""
        data = {"nodes": ["a", "b"], "edges": []}
        file_path = tmp_path / "empty.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = NetworkConfig(edges_file=str(file_path))
        state = SpatialStateFactory.from_network_config(config)
        assert len(state.locations) == 2
        assert len(state.networks["default"].edges) == 0

    def test_disconnected_graph(self, tmp_path):
        """Handles disconnected graphs."""
        data = {
            "nodes": ["a", "b", "c", "d"],
            "edges": [["a", "b"], ["c", "d"]],  # Two components
        }
        file_path = tmp_path / "disconnected.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = NetworkConfig(edges_file=str(file_path))
        state = SpatialStateFactory.from_network_config(config)
        assert len(state.locations) == 4
        assert len(state.networks["default"].edges) == 2

    def test_large_network(self, tmp_path):
        """Handles large networks efficiently."""
        nodes = [f"node_{i}" for i in range(1000)]
        edges = [[f"node_{i}", f"node_{i+1}"] for i in range(999)]
        data = {"nodes": nodes, "edges": edges}
        file_path = tmp_path / "large.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        config = NetworkConfig(edges_file=str(file_path))
        state = SpatialStateFactory.from_network_config(config)
        assert len(state.locations) == 1000
        assert len(state.networks["default"].edges) == 999
