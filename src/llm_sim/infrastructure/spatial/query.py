"""Spatial query operations for read-only spatial state access."""

from typing import Any, List, Optional

import structlog

from llm_sim.models.state import SimulationState, SpatialState

logger = structlog.get_logger(__name__)


class SpatialQuery:
    """Read-only spatial query operations."""

    @staticmethod
    def get_neighbors(
        spatial_state: Optional[SpatialState],
        location: str,
        network: str = "default"
    ) -> List[str]:
        """Get neighboring locations via specified network.

        Args:
            spatial_state: Current spatial state (may be None)
            location: Location ID to find neighbors for
            network: Network name to use for adjacency (default: "default")

        Returns:
            List of neighboring location IDs (empty if spatial_state None or location/network not found)
        """
        if spatial_state is None:
            return []

        if location not in spatial_state.locations:
            return []

        if network not in spatial_state.networks:
            return []

        # Find all edges from this location in the network
        # Edges are stored once as sorted tuples, so we check both positions
        network_state = spatial_state.networks[network]
        neighbors = []

        for loc1, loc2 in network_state.edges:
            if loc1 == location and loc2 != location:
                neighbors.append(loc2)
            elif loc2 == location and loc1 != location:
                neighbors.append(loc1)

        return neighbors

    @staticmethod
    def get_distance(
        spatial_state: Optional[SpatialState],
        loc1: str,
        loc2: str,
        network: str = "default"
    ) -> int:
        """Compute distance (hops) between locations.

        Args:
            spatial_state: Current spatial state (may be None)
            loc1: Source location ID
            loc2: Target location ID
            network: Network name to use for pathfinding (default: "default")

        Returns:
            Shortest path length in hops (0 if same location, -1 if no path or invalid inputs)
        """
        if spatial_state is None:
            return -1

        if loc1 not in spatial_state.locations or loc2 not in spatial_state.locations:
            return -1

        if network not in spatial_state.networks:
            return -1

        if loc1 == loc2:
            return 0

        # Use NetworkX to compute shortest path
        try:
            import networkx as nx
        except ImportError:
            logger.error("NetworkX not installed. Cannot compute distances.")
            return -1

        # Build graph from edge list
        network_state = spatial_state.networks[network]
        G = nx.Graph()
        G.add_edges_from(network_state.edges)

        # Compute shortest path
        try:
            path_length = nx.shortest_path_length(G, source=loc1, target=loc2)
            return path_length
        except nx.NetworkXNoPath:
            return -1
        except nx.NodeNotFound:
            return -1

    @staticmethod
    def is_adjacent(
        spatial_state: Optional[SpatialState],
        loc1: str,
        loc2: str,
        network: str = "default"
    ) -> bool:
        """Check if two locations are directly connected.

        Args:
            spatial_state: Current spatial state (may be None)
            loc1: First location ID
            loc2: Second location ID
            network: Network name to check (default: "default")

        Returns:
            True if directly connected, False otherwise
        """
        if spatial_state is None:
            return False

        if loc1 not in spatial_state.locations or loc2 not in spatial_state.locations:
            return False

        if network not in spatial_state.networks:
            return False

        if loc1 == loc2:
            return True

        # Check if edge exists in network (edges stored as sorted tuples)
        network_state = spatial_state.networks[network]
        edge = tuple(sorted([loc1, loc2]))
        return edge in network_state.edges

    @staticmethod
    def shortest_path(
        spatial_state: Optional[SpatialState],
        loc1: str,
        loc2: str,
        network: str = "default"
    ) -> List[str]:
        """Find shortest path between locations.

        Args:
            spatial_state: Current spatial state (may be None)
            loc1: Source location ID
            loc2: Target location ID
            network: Network name to use for pathfinding (default: "default")

        Returns:
            List of location IDs from loc1 to loc2 (empty if no path, [loc1] if same location)
        """
        if spatial_state is None:
            return []

        if loc1 not in spatial_state.locations or loc2 not in spatial_state.locations:
            return []

        if network not in spatial_state.networks:
            return []

        if loc1 == loc2:
            return [loc1]

        # Use NetworkX to compute shortest path
        try:
            import networkx as nx
        except ImportError:
            logger.error("NetworkX not installed. Cannot compute shortest path.")
            return []

        # Build graph from edge list
        network_state = spatial_state.networks[network]
        G = nx.Graph()
        G.add_edges_from(network_state.edges)

        # Compute shortest path
        try:
            path = nx.shortest_path(G, source=loc1, target=loc2)
            return list(path)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    @staticmethod
    def get_agent_position(
        spatial_state: Optional[SpatialState],
        agent_name: str
    ) -> Optional[str]:
        """Get agent's current location.

        Args:
            spatial_state: Current spatial state (may be None)
            agent_name: Name of agent

        Returns:
            Location ID where agent is positioned (None if not found or spatial_state None)
        """
        if spatial_state is None:
            return None

        return spatial_state.agent_positions.get(agent_name)

    @staticmethod
    def get_agents_at(
        spatial_state: Optional[SpatialState],
        location: str
    ) -> List[str]:
        """Get all agents at a specific location.

        Args:
            spatial_state: Current spatial state (may be None)
            location: Location ID to check

        Returns:
            List of agent names at the location (empty if none or location not found)
        """
        if spatial_state is None:
            return []

        if location not in spatial_state.locations:
            return []

        # Find all agents at this location
        agents = [
            agent_name
            for agent_name, agent_loc in spatial_state.agent_positions.items()
            if agent_loc == location
        ]

        return agents

    @staticmethod
    def get_agents_within(
        spatial_state: Optional[SpatialState],
        location: str,
        radius: int,
        network: str = "default"
    ) -> List[str]:
        """Get agents within radius hops of location.

        Args:
            spatial_state: Current spatial state (may be None)
            location: Center location ID
            radius: Maximum distance in hops
            network: Network name to use for distance calculation (default: "default")

        Returns:
            List of agent names within radius (empty if spatial_state None or location not found)
        """
        if spatial_state is None:
            return []

        if location not in spatial_state.locations:
            return []

        # Find all agents within radius
        agents_within = []

        for agent_name, agent_loc in spatial_state.agent_positions.items():
            distance = SpatialQuery.get_distance(spatial_state, location, agent_loc, network)
            if distance >= 0 and distance <= radius:
                agents_within.append(agent_name)

        return agents_within

    @staticmethod
    def get_location_attribute(
        spatial_state: Optional[SpatialState],
        location: str,
        key: str
    ) -> Optional[Any]:
        """Get attribute value for location.

        Args:
            spatial_state: Current spatial state (may be None)
            location: Location ID
            key: Attribute key

        Returns:
            Attribute value (None if spatial_state None, location not found, or key not present)
        """
        if spatial_state is None:
            return None

        if location not in spatial_state.locations:
            return None

        location_state = spatial_state.locations[location]
        return location_state.attributes.get(key)

    @staticmethod
    def get_locations_by_attribute(
        spatial_state: Optional[SpatialState],
        key: str,
        value: Any
    ) -> List[str]:
        """Find all locations where attribute matches value.

        Args:
            spatial_state: Current spatial state (may be None)
            key: Attribute key to match
            value: Attribute value to match

        Returns:
            List of location IDs matching the attribute (empty if spatial_state None)
        """
        if spatial_state is None:
            return []

        matching_locations = []

        for loc_id, location_state in spatial_state.locations.items():
            if key in location_state.attributes and location_state.attributes[key] == value:
                matching_locations.append(loc_id)

        return matching_locations

    @staticmethod
    def has_connection(
        spatial_state: Optional[SpatialState],
        loc1: str,
        loc2: str,
        network: str
    ) -> bool:
        """Check if connection exists in network.

        Args:
            spatial_state: Current spatial state (may be None)
            loc1: First location ID
            loc2: Second location ID
            network: Network name to check

        Returns:
            True if connection exists, False otherwise
        """
        if spatial_state is None:
            return False

        if network not in spatial_state.networks:
            return False

        if loc1 == loc2:
            return True

        # Check if edge exists in network (edges stored as sorted tuples)
        network_state = spatial_state.networks[network]
        edge = tuple(sorted([loc1, loc2]))
        return edge in network_state.edges

    @staticmethod
    def get_connection_attribute(
        spatial_state: Optional[SpatialState],
        loc1: str,
        loc2: str,
        key: str
    ) -> Optional[Any]:
        """Get attribute value for connection.

        Args:
            spatial_state: Current spatial state (may be None)
            loc1: First location ID
            loc2: Second location ID
            key: Attribute key

        Returns:
            Attribute value (None if spatial_state None, connection not found, or key not present)
        """
        if spatial_state is None:
            return None

        # Check both directions for bidirectional connections
        connection = spatial_state.connections.get((loc1, loc2))
        if connection is None:
            connection = spatial_state.connections.get((loc2, loc1))

        if connection is None:
            return None

        return connection.attributes.get(key)

    @staticmethod
    def filter_state_by_proximity(
        agent_name: str,
        state: SimulationState,
        radius: int,
        network: str = "default"
    ) -> SimulationState:
        """Return filtered state containing only nearby agents/locations.

        Args:
            agent_name: Name of the agent whose perspective to filter from
            state: Full simulation state
            radius: Maximum distance in hops
            network: Network name to use for distance calculation (default: "default")

        Returns:
            Filtered simulation state with only nearby agents and locations
        """
        if state.spatial_state is None:
            return state

        # Get agent's location
        agent_location = SpatialQuery.get_agent_position(state.spatial_state, agent_name)
        if agent_location is None:
            # Agent not positioned, return unmodified state
            return state

        # Find all locations within radius
        try:
            import networkx as nx
        except ImportError:
            logger.error("NetworkX not installed. Cannot filter by proximity.")
            return state

        network_state = state.spatial_state.networks.get(network)
        if network_state is None:
            return state

        # Build graph
        G = nx.Graph()
        G.add_edges_from(network_state.edges)

        # Find all locations within radius using BFS
        nearby_locations = set()
        if agent_location in G:
            try:
                # Get all shortest path lengths from agent location
                lengths = nx.single_source_shortest_path_length(G, agent_location, cutoff=radius)
                nearby_locations = set(lengths.keys())
            except Exception as e:
                logger.warning(f"Failed to compute proximity: {e}")
                nearby_locations = {agent_location}
        else:
            nearby_locations = {agent_location}

        # Filter locations
        filtered_locations = {
            loc_id: loc_state
            for loc_id, loc_state in state.spatial_state.locations.items()
            if loc_id in nearby_locations
        }

        # Filter agents (only keep agents at nearby locations)
        filtered_agents = {
            name: agent_state
            for name, agent_state in state.agents.items()
            if SpatialQuery.get_agent_position(state.spatial_state, name) in nearby_locations
        }

        # Create filtered spatial state
        filtered_spatial_state = state.spatial_state.model_copy(
            update={"locations": filtered_locations}
        )

        # Create filtered simulation state
        return state.model_copy(
            update={
                "agents": filtered_agents,
                "spatial_state": filtered_spatial_state
            }
        )
