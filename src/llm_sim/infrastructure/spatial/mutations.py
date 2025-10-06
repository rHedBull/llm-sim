"""Spatial mutation operations for modifying spatial state."""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import structlog

from llm_sim.models.state import ConnectionState, LocationState, NetworkState, SpatialState

logger = structlog.get_logger(__name__)


class SpatialMutations:
    """Mutation operations for spatial state (immutable updates)."""

    @staticmethod
    def move_agent(
        spatial_state: SpatialState,
        agent_name: str,
        new_location: str
    ) -> SpatialState:
        """Move agent to new location.

        Args:
            spatial_state: Current spatial state
            agent_name: Name of agent to move
            new_location: Target location ID

        Returns:
            New SpatialState with updated agent position

        Raises:
            ValueError: If new_location not in locations
        """
        if new_location not in spatial_state.locations:
            valid_locations = sorted(spatial_state.locations.keys())
            raise ValueError(
                f"Cannot move agent '{agent_name}' to invalid location '{new_location}'. "
                f"Valid locations: {valid_locations}. "
                f"Remediation: Ensure location exists in spatial topology."
            )

        # Update agent positions
        updated_positions = dict(spatial_state.agent_positions)
        updated_positions[agent_name] = new_location

        return spatial_state.model_copy(update={"agent_positions": updated_positions})

    @staticmethod
    def move_agents_batch(
        spatial_state: SpatialState,
        moves: Dict[str, str]
    ) -> SpatialState:
        """Move multiple agents at once.

        Args:
            spatial_state: Current spatial state
            moves: Map of agent_name -> new_location

        Returns:
            New SpatialState with all agent positions updated

        Raises:
            ValueError: If any location invalid (no partial updates)
        """
        # Validate all locations first (all-or-nothing)
        valid_locations = set(spatial_state.locations.keys())
        invalid_moves = []

        for agent_name, new_location in moves.items():
            if new_location not in valid_locations:
                invalid_moves.append((agent_name, new_location))

        if invalid_moves:
            valid_locations_list = sorted(valid_locations)
            invalid_desc = ", ".join([f"{agent} -> {loc}" for agent, loc in invalid_moves])
            raise ValueError(
                f"Cannot move agents: invalid locations in batch move [{invalid_desc}]. "
                f"Valid locations: {valid_locations_list}. "
                f"Remediation: Ensure all target locations exist in spatial topology."
            )

        # Apply all moves
        updated_positions = dict(spatial_state.agent_positions)
        updated_positions.update(moves)

        return spatial_state.model_copy(update={"agent_positions": updated_positions})

    @staticmethod
    def set_location_attribute(
        spatial_state: SpatialState,
        location: str,
        key: str,
        value: Any
    ) -> SpatialState:
        """Set attribute value for location.

        Args:
            spatial_state: Current spatial state
            location: Location ID
            key: Attribute key
            value: Attribute value

        Returns:
            New SpatialState with updated location attribute

        Raises:
            ValueError: If location not in locations
        """
        if location not in spatial_state.locations:
            valid_locations = sorted(spatial_state.locations.keys())
            raise ValueError(
                f"Cannot set attribute for invalid location '{location}'. "
                f"Valid locations: {valid_locations}. "
                f"Remediation: Ensure location exists in spatial topology."
            )

        # Update location attributes
        location_state = spatial_state.locations[location]
        updated_attributes = dict(location_state.attributes)
        updated_attributes[key] = value

        # Create new LocationState
        updated_location = location_state.model_copy(update={"attributes": updated_attributes})

        # Update locations dict
        updated_locations = dict(spatial_state.locations)
        updated_locations[location] = updated_location

        return spatial_state.model_copy(update={"locations": updated_locations})

    @staticmethod
    def update_location_attributes(
        spatial_state: SpatialState,
        location: str,
        updates: Dict[str, Any]
    ) -> SpatialState:
        """Update multiple attributes for location.

        Args:
            spatial_state: Current spatial state
            location: Location ID
            updates: Map of attribute keys to values

        Returns:
            New SpatialState with updated location attributes

        Raises:
            ValueError: If location not in locations
        """
        if location not in spatial_state.locations:
            valid_locations = sorted(spatial_state.locations.keys())
            raise ValueError(
                f"Cannot update attributes for invalid location '{location}'. "
                f"Valid locations: {valid_locations}. "
                f"Remediation: Ensure location exists in spatial topology."
            )

        # Update location attributes
        location_state = spatial_state.locations[location]
        updated_attributes = {**location_state.attributes, **updates}

        # Create new LocationState
        updated_location = location_state.model_copy(update={"attributes": updated_attributes})

        # Update locations dict
        updated_locations = dict(spatial_state.locations)
        updated_locations[location] = updated_location

        return spatial_state.model_copy(update={"locations": updated_locations})

    @staticmethod
    def add_connection(
        spatial_state: SpatialState,
        loc1: str,
        loc2: str,
        network: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> SpatialState:
        """Add connection to network.

        Args:
            spatial_state: Current spatial state
            loc1: First location ID
            loc2: Second location ID
            network: Network name
            attributes: Optional connection attributes

        Returns:
            New SpatialState with connection added

        Raises:
            ValueError: If locations invalid or network not found
        """
        if loc1 not in spatial_state.locations or loc2 not in spatial_state.locations:
            valid_locations = sorted(spatial_state.locations.keys())
            raise ValueError(
                f"Cannot add connection between invalid locations '{loc1}' and '{loc2}'. "
                f"Valid locations: {valid_locations}. "
                f"Remediation: Ensure both locations exist in spatial topology."
            )

        if network not in spatial_state.networks:
            valid_networks = sorted(spatial_state.networks.keys())
            raise ValueError(
                f"Cannot add connection to invalid network '{network}'. "
                f"Valid networks: {valid_networks}. "
                f"Remediation: Create network first or use existing network."
            )

        # Update network edges (add once, sorted to avoid duplicates)
        network_state = spatial_state.networks[network]
        updated_edges = set(network_state.edges)
        edge = tuple(sorted([loc1, loc2]))
        updated_edges.add(edge)

        # Create new NetworkState
        updated_network = network_state.model_copy(update={"edges": updated_edges})

        # Update networks dict
        updated_networks = dict(spatial_state.networks)
        updated_networks[network] = updated_network

        # Update connections dict if attributes provided
        updated_connections = dict(spatial_state.connections)
        if attributes is not None:
            connection = ConnectionState(
                type=network,
                attributes=attributes,
                bidirectional=True
            )
            updated_connections[(loc1, loc2)] = connection

        return spatial_state.model_copy(
            update={
                "networks": updated_networks,
                "connections": updated_connections
            }
        )

    @staticmethod
    def remove_connection(
        spatial_state: SpatialState,
        loc1: str,
        loc2: str,
        network: str
    ) -> SpatialState:
        """Remove connection from network.

        Args:
            spatial_state: Current spatial state
            loc1: First location ID
            loc2: Second location ID
            network: Network name

        Returns:
            New SpatialState with connection removed (idempotent)
        """
        if network not in spatial_state.networks:
            # Idempotent - return unchanged if network doesn't exist
            return spatial_state

        # Update network edges (remove edge regardless of order)
        network_state = spatial_state.networks[network]
        updated_edges = set(network_state.edges)
        edge = tuple(sorted([loc1, loc2]))
        updated_edges.discard(edge)

        # Create new NetworkState
        updated_network = network_state.model_copy(update={"edges": updated_edges})

        # Update networks dict
        updated_networks = dict(spatial_state.networks)
        updated_networks[network] = updated_network

        # Remove from connections dict if present
        updated_connections = dict(spatial_state.connections)
        updated_connections.pop((loc1, loc2), None)
        updated_connections.pop((loc2, loc1), None)

        return spatial_state.model_copy(
            update={
                "networks": updated_networks,
                "connections": updated_connections
            }
        )

    @staticmethod
    def update_connection_attribute(
        spatial_state: SpatialState,
        loc1: str,
        loc2: str,
        key: str,
        value: Any
    ) -> SpatialState:
        """Update connection attribute.

        Args:
            spatial_state: Current spatial state
            loc1: First location ID
            loc2: Second location ID
            key: Attribute key
            value: Attribute value

        Returns:
            New SpatialState with updated connection attribute

        Raises:
            ValueError: If connection not in connections
        """
        # Check both directions for bidirectional connections
        connection_key = None
        if (loc1, loc2) in spatial_state.connections:
            connection_key = (loc1, loc2)
        elif (loc2, loc1) in spatial_state.connections:
            connection_key = (loc2, loc1)

        if connection_key is None:
            raise ValueError(
                f"Cannot update attribute for invalid connection between '{loc1}' and '{loc2}': connection not found. "
                f"Remediation: Add connection first using add_connection()."
            )

        # Update connection attributes
        connection = spatial_state.connections[connection_key]
        updated_attributes = dict(connection.attributes)
        updated_attributes[key] = value

        # Create new ConnectionState
        updated_connection = connection.model_copy(update={"attributes": updated_attributes})

        # Update connections dict
        updated_connections = dict(spatial_state.connections)
        updated_connections[connection_key] = updated_connection

        return spatial_state.model_copy(update={"connections": updated_connections})

    @staticmethod
    def create_network(
        spatial_state: SpatialState,
        network_name: str,
        edges: Optional[Set[Tuple[str, str]]] = None
    ) -> SpatialState:
        """Create new network layer.

        Args:
            spatial_state: Current spatial state
            network_name: Name for new network
            edges: Optional initial edges (empty if None)

        Returns:
            New SpatialState with network added

        Raises:
            ValueError: If network_name already exists or edges reference invalid locations
        """
        if network_name in spatial_state.networks:
            existing_networks = sorted(spatial_state.networks.keys())
            raise ValueError(
                f"Cannot create network: network '{network_name}' already exists. "
                f"Existing networks: {existing_networks}. "
                f"Remediation: Use unique network name or update existing network."
            )

        # Validate edges if provided
        if edges:
            valid_locations = set(spatial_state.locations.keys())
            for loc1, loc2 in edges:
                if loc1 not in valid_locations or loc2 not in valid_locations:
                    valid_locations_list = sorted(valid_locations)
                    raise ValueError(
                        f"Cannot create network '{network_name}': edge ({loc1}, {loc2}) references invalid location. "
                        f"Valid locations: {valid_locations_list}. "
                        f"Remediation: Ensure all edge locations exist in spatial topology."
                    )

        # Create network
        network = NetworkState(
            name=network_name,
            edges=edges if edges else set(),
            attributes={}
        )

        # Update networks dict
        updated_networks = dict(spatial_state.networks)
        updated_networks[network_name] = network

        return spatial_state.model_copy(update={"networks": updated_networks})

    @staticmethod
    def remove_network(
        spatial_state: SpatialState,
        network_name: str
    ) -> SpatialState:
        """Remove network layer.

        Args:
            spatial_state: Current spatial state
            network_name: Name of network to remove

        Returns:
            New SpatialState with network removed (idempotent)

        Raises:
            ValueError: If attempting to remove "default" network
        """
        if network_name == "default":
            raise ValueError(
                "Cannot remove protected network 'default': default network is required for spatial topology. "
                "Remediation: The default network is required for spatial topology."
            )

        if network_name not in spatial_state.networks:
            # Idempotent - return unchanged if network doesn't exist
            return spatial_state

        # Remove network
        updated_networks = dict(spatial_state.networks)
        del updated_networks[network_name]

        return spatial_state.model_copy(update={"networks": updated_networks})

    @staticmethod
    def apply_to_region(
        spatial_state: SpatialState,
        locations: List[str],
        update_fn: Callable[[LocationState], Dict[str, Any]]
    ) -> SpatialState:
        """Apply update function to all locations in region.

        Args:
            spatial_state: Current spatial state
            locations: List of location IDs to update
            update_fn: Function that takes LocationState and returns attribute updates dict

        Returns:
            New SpatialState with all locations updated

        Raises:
            ValueError: If any location not in locations
        """
        # Validate all locations first (all-or-nothing)
        valid_locations = set(spatial_state.locations.keys())
        invalid_locations = [loc for loc in locations if loc not in valid_locations]

        if invalid_locations:
            valid_locations_list = sorted(valid_locations)
            raise ValueError(
                f"Cannot apply updates: invalid locations {invalid_locations}. "
                f"Valid locations: {valid_locations_list}. "
                f"Remediation: Ensure all locations exist in spatial topology."
            )

        # Apply updates
        updated_locations = dict(spatial_state.locations)

        for location in locations:
            location_state = updated_locations[location]
            # Get updates from function
            updates = update_fn(location_state)
            # Merge into attributes
            updated_attributes = {**location_state.attributes, **updates}
            # Create new LocationState
            updated_locations[location] = location_state.model_copy(
                update={"attributes": updated_attributes}
            )

        return spatial_state.model_copy(update={"locations": updated_locations})
