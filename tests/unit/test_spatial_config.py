"""Unit tests for spatial configuration models.

Tests validate Pydantic config models defined in data-model.md:
- GridConfig
- HexGridConfig
- NetworkConfig
- GeoJSONConfig
- SpatialConfig
- SimulationConfig extensions
"""

import pytest
import tempfile
from pathlib import Path
from pydantic import ValidationError

from llm_sim.models.config import (
    GridConfig,
    HexGridConfig,
    NetworkConfig,
    GeoJSONConfig,
    SpatialConfig,
    SimulationConfig,
    AgentConfig,
)


class TestGridConfig:
    """Tests for GridConfig model."""

    def test_create_minimal_grid_config(self):
        """Create grid config with required fields."""
        config = GridConfig(width=10, height=10)
        assert config.width == 10
        assert config.height == 10
        assert config.connectivity == 4  # Default
        assert config.wrapping is False  # Default
        assert config.type == "grid"

    def test_create_grid_with_eight_connectivity(self):
        """Create grid with 8-connectivity."""
        config = GridConfig(width=10, height=10, connectivity=8)
        assert config.connectivity == 8

    def test_create_wrapping_grid(self):
        """Create toroidal (wrapping) grid."""
        config = GridConfig(width=10, height=10, wrapping=True)
        assert config.wrapping is True

    def test_width_must_be_positive(self):
        """Width validation: must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            GridConfig(width=0, height=10)

    def test_height_must_be_positive(self):
        """Height validation: must be > 0."""
        with pytest.raises(ValidationError, match="greater than 0"):
            GridConfig(width=10, height=0)

    def test_connectivity_must_be_four_or_eight(self):
        """Connectivity validation: must be 4 or 8."""
        with pytest.raises(ValidationError):
            GridConfig(width=10, height=10, connectivity=6)  # type: ignore

    def test_type_is_always_grid(self):
        """Type field is always 'grid'."""
        config = GridConfig(width=10, height=10)
        assert config.type == "grid"


class TestHexGridConfig:
    """Tests for HexGridConfig model."""

    def test_create_minimal_hex_config(self):
        """Create hex grid config with required fields."""
        config = HexGridConfig(radius=5)
        assert config.radius == 5
        assert config.coord_system == "axial"  # Default
        assert config.type == "hex_grid"

    def test_radius_must_be_positive(self):
        """Radius validation: must be >= 0."""
        # HexGridConfig now allows radius=0 (single hex)
        config = HexGridConfig(radius=0)
        assert config.radius == 0

        # Negative radius should still fail
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            HexGridConfig(radius=-1)

    def test_coord_system_is_axial(self):
        """Coordinate system is 'axial'."""
        config = HexGridConfig(radius=5)
        assert config.coord_system == "axial"

    def test_type_is_always_hex_grid(self):
        """Type field is always 'hex_grid'."""
        config = HexGridConfig(radius=5)
        assert config.type == "hex_grid"


class TestNetworkConfig:
    """Tests for NetworkConfig model."""

    def test_create_network_config_with_valid_file(self, tmp_path):
        """Create network config with existing file."""
        file_path = tmp_path / "edges.json"
        file_path.write_text('{"nodes": [], "edges": []}')
        config = NetworkConfig(edges_file=str(file_path))
        assert config.edges_file == str(file_path)
        assert config.type == "network"

    def test_raises_error_for_missing_file(self):
        """File validation: raises error if file doesn't exist."""
        with pytest.raises(ValidationError, match="not found|does not exist"):
            NetworkConfig(edges_file="/nonexistent/path.json")

    def test_type_is_always_network(self, tmp_path):
        """Type field is always 'network'."""
        file_path = tmp_path / "edges.json"
        file_path.write_text('{}')
        config = NetworkConfig(edges_file=str(file_path))
        assert config.type == "network"


class TestGeoJSONConfig:
    """Tests for GeoJSONConfig model."""

    def test_create_geojson_config_with_valid_file(self, tmp_path):
        """Create GeoJSON config with existing file."""
        file_path = tmp_path / "regions.geojson"
        file_path.write_text('{"type": "FeatureCollection", "features": []}')
        config = GeoJSONConfig(geojson_file=str(file_path))
        assert config.geojson_file == str(file_path)
        assert config.type == "geojson"

    def test_raises_error_for_missing_file(self):
        """File validation: raises error if file doesn't exist."""
        with pytest.raises(ValidationError, match="not found|does not exist"):
            GeoJSONConfig(geojson_file="/nonexistent/path.geojson")

    def test_type_is_always_geojson(self, tmp_path):
        """Type field is always 'geojson'."""
        file_path = tmp_path / "regions.geojson"
        file_path.write_text('{}')
        config = GeoJSONConfig(geojson_file=str(file_path))
        assert config.type == "geojson"


class TestSpatialConfig:
    """Tests for SpatialConfig model (top-level)."""

    def test_create_spatial_config_with_grid_topology(self):
        """Create spatial config with grid topology."""
        config = SpatialConfig(
            topology=GridConfig(width=10, height=10)
        )
        assert config.topology.type == "grid"
        assert config.topology.width == 10

    def test_create_spatial_config_with_hex_topology(self):
        """Create spatial config with hex grid topology."""
        config = SpatialConfig(
            topology=HexGridConfig(radius=5)
        )
        assert config.topology.type == "hex_grid"
        assert config.topology.radius == 5

    def test_create_spatial_config_with_network_topology(self, tmp_path):
        """Create spatial config with network topology."""
        file_path = tmp_path / "edges.json"
        file_path.write_text('{"nodes": [], "edges": []}')
        config = SpatialConfig(
            topology=NetworkConfig(edges_file=str(file_path))
        )
        assert config.topology.type == "network"

    def test_create_spatial_config_with_geojson_topology(self, tmp_path):
        """Create spatial config with GeoJSON topology."""
        file_path = tmp_path / "regions.geojson"
        file_path.write_text('{"type": "FeatureCollection", "features": []}')
        config = SpatialConfig(
            topology=GeoJSONConfig(geojson_file=str(file_path))
        )
        assert config.topology.type == "geojson"

    def test_discriminator_routes_by_type(self):
        """Discriminator: routes to correct config type based on 'type' field."""
        grid_data = {"type": "grid", "width": 10, "height": 10}
        hex_data = {"type": "hex_grid", "radius": 5}

        grid_config = SpatialConfig(topology=grid_data)  # type: ignore
        hex_config = SpatialConfig(topology=hex_data)  # type: ignore

        assert isinstance(grid_config.topology, GridConfig)
        assert isinstance(hex_config.topology, HexGridConfig)

    def test_location_attributes_optional(self):
        """Location attributes field is optional."""
        config = SpatialConfig(
            topology=GridConfig(width=5, height=5)
        )
        assert config.location_attributes is None

    def test_location_attributes_provided(self):
        """Location attributes can be provided."""
        config = SpatialConfig(
            topology=GridConfig(width=5, height=5),
            location_attributes={
                "0,0": {"resource": 100},
                "1,0": {"resource": 50},
            }
        )
        assert config.location_attributes["0,0"]["resource"] == 100

    def test_additional_networks_optional(self):
        """Additional networks field is optional."""
        config = SpatialConfig(
            topology=GridConfig(width=5, height=5)
        )
        assert config.additional_networks is None

    def test_additional_networks_provided(self, tmp_path):
        """Additional networks can be provided."""
        file_path = tmp_path / "rail.json"
        file_path.write_text('{"nodes": [], "edges": []}')
        config = SpatialConfig(
            topology=GridConfig(width=5, height=5),
            additional_networks=[
                {"name": "rail", "edges_file": str(file_path)}
            ]
        )
        assert len(config.additional_networks) == 1
        assert config.additional_networks[0]["name"] == "rail"


class TestAgentConfigExtension:
    """Tests for AgentConfig with initial_location field."""

    def test_create_agent_without_initial_location(self):
        """Create agent without spatial positioning."""
        agent = AgentConfig(
            name="agent_a",
            type="nation",
            initial_economic_strength=1000.0
        )
        assert agent.initial_location is None

    def test_create_agent_with_initial_location(self):
        """Create agent with initial location."""
        agent = AgentConfig(
            name="agent_a",
            type="nation",
            initial_economic_strength=1000.0,
            initial_location="winterfell"
        )
        assert agent.initial_location == "winterfell"

    def test_initial_location_is_optional(self):
        """Initial location field is optional."""
        agent = AgentConfig(name="agent_a", type="nation")
        assert agent.initial_location is None


class TestSimulationConfigExtension:
    """Tests for SimulationConfig with spatial field."""

    def test_create_simulation_config_without_spatial(self, mock_config):
        """Create simulation config without spatial topology."""
        # mock_config from conftest.py
        assert mock_config.spatial is None

    def test_create_simulation_config_with_spatial(self, mock_config):
        """Create simulation config with spatial topology."""
        spatial_config = SpatialConfig(
            topology=GridConfig(width=10, height=10)
        )
        config = mock_config.model_copy(update={"spatial": spatial_config})
        assert config.spatial is not None
        assert config.spatial.topology.type == "grid"

    def test_spatial_field_is_optional(self, mock_config):
        """Spatial field is optional."""
        assert mock_config.spatial is None

    def test_validates_agent_locations_against_spatial_topology(self):
        """Validation: agent initial_location should reference valid spatial locations.

        Note: This validation happens at orchestrator initialization, not config validation.
        This test documents the expected behavior.
        """
        # This is a reminder that validation will happen later
        spatial_config = SpatialConfig(
            topology=GridConfig(width=2, height=2)
        )
        agents = [
            AgentConfig(name="agent_a", type="nation", initial_location="0,0"),
            AgentConfig(name="agent_b", type="nation", initial_location="invalid"),
        ]
        # Config creation should succeed (validation happens later)
        from llm_sim.models.config import SimulationSettings, EngineConfig, ValidatorConfig, LoggingConfig, TerminationConditions
        config = SimulationConfig(
            simulation=SimulationSettings(name="Test", max_turns=10, termination=TerminationConditions()),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=agents,
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
            spatial=spatial_config
        )
        # Should not raise during config creation
        assert config.spatial is not None


class TestConfigSerialization:
    """Tests for config serialization/deserialization."""

    def test_grid_config_serializes_to_dict(self):
        """GridConfig serializes to dict."""
        config = GridConfig(width=10, height=10, connectivity=4, wrapping=True)
        data = config.model_dump()
        assert data["type"] == "grid"
        assert data["width"] == 10
        assert data["wrapping"] is True

    def test_spatial_config_serializes_to_dict(self):
        """SpatialConfig serializes to dict."""
        config = SpatialConfig(
            topology=GridConfig(width=10, height=10),
            location_attributes={"0,0": {"resource": 100}}
        )
        data = config.model_dump()
        assert data["topology"]["type"] == "grid"
        assert data["location_attributes"]["0,0"]["resource"] == 100

    def test_spatial_config_deserializes_from_dict(self):
        """SpatialConfig deserializes from dict."""
        data = {
            "topology": {
                "type": "grid",
                "width": 10,
                "height": 10,
                "connectivity": 4,
                "wrapping": False
            },
            "location_attributes": {"0,0": {"resource": 100}}
        }
        config = SpatialConfig(**data)
        assert isinstance(config.topology, GridConfig)
        assert config.topology.width == 10
        assert config.location_attributes["0,0"]["resource"] == 100

    def test_roundtrip_serialization(self):
        """Config can be serialized and deserialized."""
        original = SpatialConfig(
            topology=HexGridConfig(radius=5),
            location_attributes={"0,0": {"resource": 100}}
        )
        data = original.model_dump()
        restored = SpatialConfig(**data)
        assert isinstance(restored.topology, HexGridConfig)
        assert restored.topology.radius == 5
        assert restored.location_attributes["0,0"]["resource"] == 100
