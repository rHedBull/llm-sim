"""Unit tests for hexagonal grid factory.

Tests specific to hexagonal grid creation with axial coordinates.
"""

import pytest

from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.models.config import HexGridConfig
from llm_sim.models.state import SpatialState


class TestHexTopology:
    """Tests for hexagonal grid topology generation."""

    def test_creates_hexagonal_shape(self):
        """Creates hexagonal shape with given radius."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        # Radius 1: 1 center + 6 neighbors = 7 hexes
        assert len(state.locations) == 7

    def test_radius_zero_has_one_hex(self):
        """Radius 0 creates single hex."""
        config = HexGridConfig(radius=0)
        state = SpatialStateFactory.from_hex_config(config)
        assert len(state.locations) == 1
        assert "0,0" in state.locations

    def test_radius_two_has_nineteen_hexes(self):
        """Radius 2 creates 19 hexes."""
        config = HexGridConfig(radius=2)
        state = SpatialStateFactory.from_hex_config(config)
        # Formula: 3*R^2 + 3*R + 1 = 3*4 + 3*2 + 1 = 19
        assert len(state.locations) == 19


class TestAxialCoordinates:
    """Tests for axial coordinate system."""

    def test_uses_axial_coordinate_format(self):
        """Uses {q},{r} format for location IDs."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert "0,0" in state.locations  # Center

    def test_center_hex_at_origin(self):
        """Center hex at (0,0)."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert "0,0" in state.locations

    def test_creates_six_neighbors_for_center(self):
        """Center hex has 6 neighbors in radius 1."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        edges = state.networks["default"].edges
        center_edges = [e for e in edges if "0,0" in e]
        assert len(center_edges) == 6


class TestHexAdjacency:
    """Tests for hexagonal adjacency (6 neighbors)."""

    def test_interior_hex_has_six_neighbors(self):
        """Interior hexes have 6 neighbors."""
        config = HexGridConfig(radius=2)
        state = SpatialStateFactory.from_hex_config(config)
        edges = state.networks["default"].edges
        # Center hex should have 6 neighbors
        center_edges = [e for e in edges if "0,0" in e]
        assert len(center_edges) == 6

    def test_edge_hex_has_fewer_neighbors(self):
        """Edge hexes have fewer than 6 neighbors."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        edges = state.networks["default"].edges
        # Edge hexes (at radius boundary) have < 6 neighbors
        # Pick one of the edge hexes
        edge_hex_edges = [e for e in edges if "1,0" in e]
        assert len(edge_hex_edges) < 6

    def test_six_neighbor_directions(self):
        """Validates 6 neighbor directions from center."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        # Axial neighbors of (0,0): (+1,0), (-1,0), (0,+1), (0,-1), (+1,-1), (-1,+1)
        expected_neighbors = {
            "1,0", "-1,0", "0,1", "0,-1", "1,-1", "-1,1"
        }
        # All should exist in locations
        for neighbor in expected_neighbors:
            assert neighbor in state.locations


class TestDefaultNetwork:
    """Tests for default network creation."""

    def test_creates_default_network(self):
        """Always creates 'default' network."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert "default" in state.networks

    def test_default_network_contains_hex_adjacency(self):
        """Default network contains hexagonal adjacency edges."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert len(state.networks["default"].edges) > 0


class TestInitialization:
    """Tests for state initialization."""

    def test_agent_positions_empty(self):
        """Agent positions initialized empty."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert state.agent_positions == {}

    def test_topology_type_is_hex_grid(self):
        """Topology type set to 'hex_grid'."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert state.topology_type == "hex_grid"

    def test_returns_valid_spatial_state(self):
        """Returns valid SpatialState instance."""
        config = HexGridConfig(radius=1)
        state = SpatialStateFactory.from_hex_config(config)
        assert isinstance(state, SpatialState)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_large_hex_grid(self):
        """Handles large radius hex grids."""
        config = HexGridConfig(radius=10)
        state = SpatialStateFactory.from_hex_config(config)
        # Formula: 3*R^2 + 3*R + 1 = 3*100 + 3*10 + 1 = 331
        assert len(state.locations) == 331

    def test_all_hexes_have_valid_coordinates(self):
        """All generated hexes have valid axial coordinates."""
        config = HexGridConfig(radius=2)
        state = SpatialStateFactory.from_hex_config(config)
        for loc_id in state.locations:
            # Should be in format "q,r"
            parts = loc_id.split(",")
            assert len(parts) == 2
            q, r = int(parts[0]), int(parts[1])
            # Valid axial: max(|q|, |r|, |q+r|) <= radius
            assert max(abs(q), abs(r), abs(q + r)) <= 2
