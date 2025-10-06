"""Spatial state factory for creating topologies from configuration."""

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import structlog

from llm_sim.models.config import (
    GeoJSONConfig,
    GridConfig,
    HexGridConfig,
    NetworkConfig,
    SpatialConfig,
)
from llm_sim.models.state import (
    LocationState,
    NetworkState,
    SpatialState,
)

logger = structlog.get_logger(__name__)


# Hexagonal grid neighbor offsets (axial coordinates)
HEX_AXIAL_NEIGHBORS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]


class SpatialStateFactory:
    """Factory for creating SpatialState from configuration."""

    @staticmethod
    def create(config: SpatialConfig) -> SpatialState:
        """Create SpatialState from config by dispatching to specific factory.

        Args:
            config: Spatial configuration containing topology and optional attributes

        Returns:
            Valid SpatialState instance

        Raises:
            ValueError: If topology type unknown or configuration invalid
        """
        topology_type = config.topology.type

        # Dispatch to appropriate factory
        if topology_type == "grid":
            spatial_state = SpatialStateFactory.from_grid_config(config.topology)
        elif topology_type == "hex_grid":
            spatial_state = SpatialStateFactory.from_hex_config(config.topology)
        elif topology_type == "network":
            spatial_state = SpatialStateFactory.from_network_config(config.topology)
        elif topology_type == "geojson":
            spatial_state = SpatialStateFactory.from_geojson(config.topology)
        else:
            raise ValueError(
                f"Unknown topology type '{topology_type}'. "
                f"Supported types: grid, hex_grid, network, geojson. "
                f"Remediation: Set spatial.topology.type to a supported value in config."
            )

        # Apply location attributes if provided
        if config.location_attributes:
            spatial_state = SpatialStateFactory._apply_location_attributes(
                spatial_state, config.location_attributes
            )

        # Create additional networks if provided
        if config.additional_networks:
            spatial_state = SpatialStateFactory._create_additional_networks(
                spatial_state, config.additional_networks
            )

        return spatial_state

    @staticmethod
    def from_grid_config(config: GridConfig) -> SpatialState:
        """Build 2D square grid topology.

        Args:
            config: Grid configuration with width, height, connectivity, wrapping

        Returns:
            SpatialState with grid topology

        Raises:
            ValueError: If configuration invalid
        """
        if config.width <= 0:
            raise ValueError(
                f"Failed to create grid topology: width must be positive, got {config.width}. "
                f"Remediation: Set spatial.topology.width to positive integer in config."
            )
        if config.height <= 0:
            raise ValueError(
                f"Failed to create grid topology: height must be positive, got {config.height}. "
                f"Remediation: Set spatial.topology.height to positive integer in config."
            )

        # Create locations
        locations: Dict[str, LocationState] = {}
        for y in range(config.height):
            for x in range(config.width):
                loc_id = f"{x},{y}"
                locations[loc_id] = LocationState(id=loc_id)

        # Create edges for default network
        edges: Set[Tuple[str, str]] = set()

        for y in range(config.height):
            for x in range(config.width):
                loc_id = f"{x},{y}"

                # 4-connectivity: cardinal directions
                neighbors = []
                if config.connectivity == 4:
                    neighbors = [
                        (x + 1, y),  # right
                        (x, y + 1),  # down
                        (x - 1, y),  # left
                        (x, y - 1),  # up
                    ]
                elif config.connectivity == 8:
                    # 8-connectivity: cardinal + diagonal directions
                    neighbors = [
                        (x + 1, y),      # right
                        (x + 1, y + 1),  # down-right
                        (x, y + 1),      # down
                        (x - 1, y + 1),  # down-left
                        (x - 1, y),      # left
                        (x - 1, y - 1),  # up-left
                        (x, y - 1),      # up
                        (x + 1, y - 1),  # up-right
                    ]

                # Add valid neighbors
                for nx, ny in neighbors:
                    if config.wrapping:
                        # Wrap coordinates
                        nx = nx % config.width
                        ny = ny % config.height
                        neighbor_id = f"{nx},{ny}"
                        # Add edge once (sorted to avoid duplicates)
                        edge = tuple(sorted([loc_id, neighbor_id]))
                        edges.add(edge)
                    else:
                        # Check bounds
                        if 0 <= nx < config.width and 0 <= ny < config.height:
                            neighbor_id = f"{nx},{ny}"
                            # Add edge once (sorted to avoid duplicates)
                            edge = tuple(sorted([loc_id, neighbor_id]))
                            edges.add(edge)

        # Create default network
        networks = {
            "default": NetworkState(
                name="default",
                edges=edges,
                attributes={"connectivity": config.connectivity, "wrapping": config.wrapping}
            )
        }

        return SpatialState(
            topology_type="grid",
            agent_positions={},
            locations=locations,
            connections={},
            networks=networks
        )

    @staticmethod
    def from_hex_config(config: HexGridConfig) -> SpatialState:
        """Build hexagonal grid topology using axial coordinates.

        Args:
            config: Hex grid configuration with radius

        Returns:
            SpatialState with hexagonal grid topology

        Raises:
            ValueError: If configuration invalid
        """
        if config.radius < 0:
            raise ValueError(
                f"Failed to create hex grid topology: radius must be non-negative, got {config.radius}. "
                f"Remediation: Set spatial.topology.radius to non-negative integer in config."
            )

        # Create locations using axial coordinates
        locations: Dict[str, LocationState] = {}
        for q in range(-config.radius, config.radius + 1):
            r1 = max(-config.radius, -q - config.radius)
            r2 = min(config.radius, -q + config.radius)
            for r in range(r1, r2 + 1):
                loc_id = f"{q},{r}"
                locations[loc_id] = LocationState(
                    id=loc_id,
                    metadata={"q": q, "r": r, "coord_system": "axial"}
                )

        # Create edges for default network (6 neighbors per hex)
        edges: Set[Tuple[str, str]] = set()
        for loc_id in locations.keys():
            q, r = map(int, loc_id.split(","))

            # Add 6 neighbors
            for dq, dr in HEX_AXIAL_NEIGHBORS:
                nq, nr = q + dq, r + dr
                neighbor_id = f"{nq},{nr}"

                if neighbor_id in locations:
                    # Add edge once (sorted to avoid duplicates)
                    edge = tuple(sorted([loc_id, neighbor_id]))
                    edges.add(edge)

        # Create default network
        networks = {
            "default": NetworkState(
                name="default",
                edges=edges,
                attributes={"coord_system": "axial", "radius": config.radius}
            )
        }

        return SpatialState(
            topology_type="hex_grid",
            agent_positions={},
            locations=locations,
            connections={},
            networks=networks
        )

    @staticmethod
    def from_network_config(config: NetworkConfig) -> SpatialState:
        """Build arbitrary graph topology from edge list file.

        Args:
            config: Network configuration with path to edge list JSON file

        Returns:
            SpatialState with network topology

        Raises:
            ValueError: If file not found or malformed
        """
        edges_file = Path(config.edges_file)
        if not edges_file.exists():
            raise ValueError(
                f"Failed to create network topology: edges file not found at {config.edges_file}. "
                f"Remediation: Ensure file exists or update spatial.topology.edges_file path."
            )

        try:
            with open(edges_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to create network topology: malformed JSON in {config.edges_file}. "
                f"Error: {e}. "
                f"Remediation: Ensure file contains valid JSON with 'nodes' and 'edges' fields."
            )

        # Validate required fields
        if "nodes" not in data:
            raise ValueError(
                f"Failed to create network topology: missing 'nodes' field in {config.edges_file}. "
                f"Remediation: Add 'nodes' array to JSON file."
            )
        if "edges" not in data:
            raise ValueError(
                f"Failed to create network topology: missing 'edges' field in {config.edges_file}. "
                f"Remediation: Add 'edges' array to JSON file."
            )

        # Create locations
        locations: Dict[str, LocationState] = {}
        node_attributes = data.get("attributes", {})

        for node_id in data["nodes"]:
            attributes = node_attributes.get(node_id, {})
            locations[node_id] = LocationState(id=node_id, attributes=attributes)

        # Create edges
        edges: Set[Tuple[str, str]] = set()
        for edge in data["edges"]:
            if len(edge) != 2:
                raise ValueError(
                    f"Failed to create network topology: invalid edge {edge} in {config.edges_file}. "
                    f"Each edge must be a 2-element array [source, target]. "
                    f"Remediation: Fix edge format in JSON file."
                )
            loc1, loc2 = edge
            if loc1 not in locations or loc2 not in locations:
                raise ValueError(
                    f"Failed to create network topology: edge references unknown node in {edge}. "
                    f"Valid nodes: {sorted(locations.keys())}. "
                    f"Remediation: Ensure all edge nodes exist in 'nodes' array."
                )
            # Add edge once (sorted to avoid duplicates)
            edge = tuple(sorted([loc1, loc2]))
            edges.add(edge)

        # Create default network
        networks = {
            "default": NetworkState(
                name="default",
                edges=edges,
                attributes={}
            )
        }

        return SpatialState(
            topology_type="network",
            agent_positions={},
            locations=locations,
            connections={},
            networks=networks
        )

    @staticmethod
    def from_geojson(config: GeoJSONConfig) -> SpatialState:
        """Load geographic regions from GeoJSON file.

        Args:
            config: GeoJSON configuration with path to file

        Returns:
            SpatialState with region topology

        Raises:
            ValueError: If file not found, malformed, or missing required fields
        """
        geojson_file = Path(config.geojson_file)
        if not geojson_file.exists():
            raise ValueError(
                f"Failed to create GeoJSON topology: file not found at {config.geojson_file}. "
                f"Remediation: Ensure file exists or update spatial.topology.geojson_file path."
            )

        try:
            with open(geojson_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to create GeoJSON topology: malformed JSON in {config.geojson_file}. "
                f"Error: {e}. "
                f"Remediation: Ensure file contains valid JSON."
            )

        # Validate GeoJSON structure
        if data.get("type") != "FeatureCollection":
            raise ValueError(
                f"Failed to create GeoJSON topology: expected FeatureCollection, got {data.get('type')}. "
                f"Remediation: Ensure GeoJSON has type='FeatureCollection'."
            )

        features = data.get("features", [])
        if not features:
            raise ValueError(
                f"Failed to create GeoJSON topology: no features found in {config.geojson_file}. "
                f"Remediation: Add Feature objects to 'features' array."
            )

        # Import shapely for geometry operations
        try:
            from shapely.geometry import shape
        except ImportError:
            raise ValueError(
                "Failed to create GeoJSON topology: shapely library not installed. "
                "Remediation: Install with 'uv add shapely' or 'pip install shapely'."
            )

        # Parse features and compute adjacency
        locations: Dict[str, LocationState] = {}
        geometries: Dict[str, Any] = {}

        for feature in features:
            if feature.get("type") != "Feature":
                continue

            properties = feature.get("properties", {})
            if "name" not in properties:
                raise ValueError(
                    "Failed to create GeoJSON topology: feature missing 'name' property. "
                    "Remediation: Ensure all features have properties.name field."
                )

            name = properties["name"]
            if name in locations:
                raise ValueError(
                    f"Failed to create GeoJSON topology: duplicate region name '{name}'. "
                    f"Remediation: Ensure all feature names are unique."
                )

            # Create location with all properties as attributes
            locations[name] = LocationState(
                id=name,
                attributes=dict(properties)
            )

            # Parse geometry for adjacency computation
            geometry = feature.get("geometry")
            if geometry:
                try:
                    geometries[name] = shape(geometry)
                except Exception as e:
                    logger.warning(f"Failed to parse geometry for region '{name}': {e}")

        # Compute adjacency from geometries
        edges: Set[Tuple[str, str]] = set()
        region_names = list(geometries.keys())

        for i, name1 in enumerate(region_names):
            geom1 = geometries[name1]
            for name2 in region_names[i + 1:]:
                geom2 = geometries[name2]

                # Check if geometries touch or share boundary
                try:
                    if geom1.touches(geom2) or (geom1.intersects(geom2) and not geom1.equals(geom2)):
                        # Add edge once (sorted to avoid duplicates)
                        edge = tuple(sorted([name1, name2]))
                        edges.add(edge)
                except Exception as e:
                    logger.warning(f"Failed to compute adjacency between '{name1}' and '{name2}': {e}")

        # Create default network
        networks = {
            "default": NetworkState(
                name="default",
                edges=edges,
                attributes={"source": "geojson"}
            )
        }

        return SpatialState(
            topology_type="regions",
            agent_positions={},
            locations=locations,
            connections={},
            networks=networks
        )

    @staticmethod
    def _apply_location_attributes(
        spatial_state: SpatialState,
        location_attributes: Dict[str, Dict[str, Any]]
    ) -> SpatialState:
        """Override/augment location attributes from config.

        Args:
            spatial_state: Current spatial state
            location_attributes: Map of location_id -> attributes to merge

        Returns:
            New SpatialState with updated location attributes
        """
        updated_locations = dict(spatial_state.locations)

        for loc_id, attributes in location_attributes.items():
            if loc_id not in updated_locations:
                logger.warning(
                    f"Location attribute override for unknown location '{loc_id}'. "
                    f"Valid locations: {sorted(spatial_state.locations.keys())}. Skipping."
                )
                continue

            # Merge attributes (config overrides existing)
            existing_location = updated_locations[loc_id]
            merged_attributes = {**existing_location.attributes, **attributes}

            # Create new LocationState with merged attributes
            updated_locations[loc_id] = existing_location.model_copy(
                update={"attributes": merged_attributes}
            )

        return spatial_state.model_copy(update={"locations": updated_locations})

    @staticmethod
    def _create_additional_networks(
        spatial_state: SpatialState,
        networks: List[Dict[str, Any]]
    ) -> SpatialState:
        """Add extra network layers beyond base topology.

        Args:
            spatial_state: Current spatial state
            networks: List of network definitions (each with 'name' and 'edges_file')

        Returns:
            New SpatialState with additional networks added

        Raises:
            ValueError: If network definition invalid or edges reference unknown locations
        """
        updated_networks = dict(spatial_state.networks)

        for network_def in networks:
            if "name" not in network_def:
                raise ValueError(
                    "Failed to create additional network: missing 'name' field in network definition. "
                    "Remediation: Add 'name' field to each network in spatial.additional_networks."
                )
            if "edges_file" not in network_def:
                raise ValueError(
                    f"Failed to create additional network '{network_def['name']}': missing 'edges_file'. "
                    f"Remediation: Add 'edges_file' field to network definition."
                )

            network_name = network_def["name"]
            if network_name in updated_networks:
                raise ValueError(
                    f"Failed to create additional network: network '{network_name}' already exists. "
                    f"Remediation: Use unique network names."
                )

            edges_file = Path(network_def["edges_file"])
            if not edges_file.exists():
                raise ValueError(
                    f"Failed to create additional network '{network_name}': edges file not found at {edges_file}. "
                    f"Remediation: Ensure file exists or update edges_file path."
                )

            try:
                with open(edges_file, 'r') as f:
                    edge_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to create additional network '{network_name}': malformed JSON in {edges_file}. "
                    f"Error: {e}. Remediation: Ensure file contains valid JSON."
                )

            if "edges" not in edge_data:
                raise ValueError(
                    f"Failed to create additional network '{network_name}': missing 'edges' field in {edges_file}. "
                    f"Remediation: Add 'edges' array to JSON file."
                )

            # Parse edges
            edges: Set[Tuple[str, str]] = set()
            valid_locations = set(spatial_state.locations.keys())

            for edge in edge_data["edges"]:
                if len(edge) != 2:
                    raise ValueError(
                        f"Failed to create additional network '{network_name}': invalid edge {edge}. "
                        f"Each edge must be 2-element array. Remediation: Fix edge format."
                    )
                loc1, loc2 = edge
                if loc1 not in valid_locations or loc2 not in valid_locations:
                    raise ValueError(
                        f"Failed to create additional network '{network_name}': edge {edge} references unknown location. "
                        f"Valid locations: {sorted(valid_locations)}. "
                        f"Remediation: Ensure edge locations exist in topology."
                    )
                # Add edge once (sorted to avoid duplicates)
                edge = tuple(sorted([loc1, loc2]))
                edges.add(edge)

            # Create network
            updated_networks[network_name] = NetworkState(
                name=network_name,
                edges=edges,
                attributes=network_def.get("attributes", {})
            )

        return spatial_state.model_copy(update={"networks": updated_networks})
