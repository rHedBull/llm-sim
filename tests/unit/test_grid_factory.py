"""Unit tests for grid topology factory.

Tests specific to 2D square grid creation logic.
"""

import pytest

from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.models.config import GridConfig
from llm_sim.models.state import SpatialState


class TestGridTopology:
    """Tests for grid topology generation."""

    def test_creates_all_grid_cells(self):
        """Creates width × height locations."""
        config = GridConfig(width=3, height=4, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert len(state.locations) == 12

    def test_uses_correct_coordinate_format(self):
        """Uses {x},{y} format for location IDs."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        expected_ids = {"0,0", "1,0", "0,1", "1,1"}
        assert set(state.locations.keys()) == expected_ids

    def test_origin_at_top_left(self):
        """Origin (0,0) at top-left corner."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert "0,0" in state.locations


class TestFourConnectivity:
    """Tests for 4-way connectivity (cardinal directions)."""

    def test_interior_cell_has_four_neighbors(self):
        """Interior cells have 4 neighbors (N, S, E, W)."""
        config = GridConfig(width=3, height=3, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        # Center cell (1,1) should have 4 neighbors
        edges = state.networks["default"].edges
        center_edges = [e for e in edges if "1,1" in e]
        assert len(center_edges) == 4

    def test_corner_cell_has_two_neighbors(self):
        """Corner cells have 2 neighbors."""
        config = GridConfig(width=3, height=3, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        corner_edges = [e for e in edges if "0,0" in e]
        assert len(corner_edges) == 2

    def test_edge_cell_has_three_neighbors(self):
        """Edge cells (non-corner) have 3 neighbors."""
        config = GridConfig(width=3, height=3, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        edge_edges = [e for e in edges if "1,0" in e]
        assert len(edge_edges) == 3


class TestEightConnectivity:
    """Tests for 8-way connectivity (including diagonals)."""

    def test_interior_cell_has_eight_neighbors(self):
        """Interior cells have 8 neighbors with diagonals."""
        config = GridConfig(width=3, height=3, connectivity=8)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        center_edges = [e for e in edges if "1,1" in e]
        assert len(center_edges) == 8

    def test_corner_cell_has_three_neighbors(self):
        """Corner cells have 3 neighbors with diagonals."""
        config = GridConfig(width=3, height=3, connectivity=8)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        corner_edges = [e for e in edges if "0,0" in e]
        assert len(corner_edges) == 3

    def test_includes_diagonal_connections(self):
        """8-connectivity includes diagonal edges."""
        config = GridConfig(width=2, height=2, connectivity=8)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        # Should include diagonal (0,0) to (1,1)
        has_diagonal = any(
            set(e) == {"0,0", "1,1"} for e in edges
        )
        assert has_diagonal


class TestWrapping:
    """Tests for toroidal (wrapping) grids."""

    def test_wrapping_connects_opposite_edges(self):
        """Wrapping creates connections between opposite edges."""
        config = GridConfig(width=3, height=3, connectivity=4, wrapping=True)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        # Left edge should connect to right edge
        has_horizontal_wrap = any(
            set(e) == {"0,0", "2,0"} for e in edges
        )
        # Top edge should connect to bottom edge
        has_vertical_wrap = any(
            set(e) == {"0,0", "0,2"} for e in edges
        )
        assert has_horizontal_wrap or has_vertical_wrap

    def test_wrapping_increases_edge_count(self):
        """Wrapping grid has more edges than non-wrapping."""
        config_no_wrap = GridConfig(width=3, height=3, connectivity=4, wrapping=False)
        config_wrap = GridConfig(width=3, height=3, connectivity=4, wrapping=True)
        state_no_wrap = SpatialStateFactory.from_grid_config(config_no_wrap)
        state_wrap = SpatialStateFactory.from_grid_config(config_wrap)
        assert len(state_wrap.networks["default"].edges) > len(state_no_wrap.networks["default"].edges)

    def test_corner_cells_have_more_neighbors_when_wrapping(self):
        """Corner cells have 4 neighbors (not 2) when wrapping."""
        config = GridConfig(width=3, height=3, connectivity=4, wrapping=True)
        state = SpatialStateFactory.from_grid_config(config)
        edges = state.networks["default"].edges
        corner_edges = [e for e in edges if "0,0" in e]
        assert len(corner_edges) == 4


class TestDefaultNetwork:
    """Tests for default network creation."""

    def test_creates_default_network(self):
        """Always creates 'default' network."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert "default" in state.networks

    def test_default_network_contains_grid_adjacency(self):
        """Default network contains grid adjacency edges."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert len(state.networks["default"].edges) > 0


class TestInitialization:
    """Tests for state initialization."""

    def test_agent_positions_empty(self):
        """Agent positions initialized empty."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert state.agent_positions == {}

    def test_topology_type_is_grid(self):
        """Topology type set to 'grid'."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert state.topology_type == "grid"

    def test_returns_valid_spatial_state(self):
        """Returns valid SpatialState instance."""
        config = GridConfig(width=2, height=2, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert isinstance(state, SpatialState)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_cell_grid(self):
        """Handles 1×1 grid."""
        config = GridConfig(width=1, height=1, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert len(state.locations) == 1
        assert "0,0" in state.locations

    def test_one_dimensional_grids(self):
        """Handles 1×N and N×1 grids."""
        config_row = GridConfig(width=5, height=1, connectivity=4)
        config_col = GridConfig(width=1, height=5, connectivity=4)
        state_row = SpatialStateFactory.from_grid_config(config_row)
        state_col = SpatialStateFactory.from_grid_config(config_col)
        assert len(state_row.locations) == 5
        assert len(state_col.locations) == 5

    def test_large_grid(self):
        """Handles large grids efficiently."""
        config = GridConfig(width=100, height=100, connectivity=4)
        state = SpatialStateFactory.from_grid_config(config)
        assert len(state.locations) == 10000
