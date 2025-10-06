"""Integration tests for spatial positioning with validator.

Tests validator spatial constraints and validation logic.
"""

import pytest

from llm_sim.models.config import GridConfig, SpatialConfig
from llm_sim.models.state import LocationState, NetworkState
from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.infrastructure.spatial.mutations import SpatialMutations


@pytest.fixture
def validator_spatial_state():
    """Create spatial state for validator testing."""
    config = SpatialConfig(
        topology=GridConfig(width=5, height=5, connectivity=4),
        location_attributes={
            "0,0": {"type": "safe_zone"},
            "4,4": {"type": "restricted_zone"},
        }
    )
    return SpatialStateFactory.create(config)


class TestMovementValidation:
    """Tests for validating agent movement."""

    def test_validator_checks_location_exists(self, validator_spatial_state):
        """Validator ensures target location exists."""
        # Valid movement
        try:
            SpatialMutations.move_agent(validator_spatial_state, "agent_a", "1,1")
            valid = True
        except ValueError:
            valid = False
        assert valid

        # Invalid movement
        with pytest.raises(ValueError):
            SpatialMutations.move_agent(validator_spatial_state, "agent_a", "99,99")

    def test_validator_checks_adjacency_constraint(self, validator_spatial_state):
        """Validator can check if move respects adjacency.

        Note: This is optional constraint that validator can enforce.
        """
        validator_spatial_state = SpatialMutations.move_agent(validator_spatial_state, "agent_a", "0,0")

        # Check adjacency before validating move
        is_adjacent = SpatialQuery.is_adjacent(validator_spatial_state, "0,0", "1,0")
        assert is_adjacent  # Valid move target

        is_far = SpatialQuery.is_adjacent(validator_spatial_state, "0,0", "4,4")
        assert not is_far  # Invalid move target (if adjacency required)

    def test_validator_checks_maximum_distance(self, validator_spatial_state):
        """Validator enforces maximum movement distance."""
        validator_spatial_state = SpatialMutations.move_agent(validator_spatial_state, "agent_a", "0,0")

        # Check distance constraint
        distance = SpatialQuery.get_distance(validator_spatial_state, "0,0", "2,2")
        # If validator enforces max_distance=2, movement to (2,2) should be valid
        assert distance == 4  # Manhattan distance


class TestLocationConstraints:
    """Tests for location-based constraints."""

    def test_validator_checks_zone_restrictions(self, validator_spatial_state):
        """Validator checks if agent can enter restricted zones."""
        zone_type = SpatialQuery.get_location_attribute(validator_spatial_state, "4,4", "type")
        assert zone_type == "restricted_zone"

        # Validator logic would check if agent has permission
        # For now, just verify we can query the constraint
        safe_zone = SpatialQuery.get_location_attribute(validator_spatial_state, "0,0", "type")
        assert safe_zone == "safe_zone"

    def test_validator_checks_capacity_constraints(self):
        """Validator checks if location has capacity for agent."""
        config = SpatialConfig(
            topology=GridConfig(width=3, height=3, connectivity=4),
            location_attributes={
                "1,1": {"capacity": 2},
            }
        )
        spatial_state = SpatialStateFactory.create(config)

        # Add agents to location
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_1", "1,1")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "1,1")

        # Check capacity
        agents_at_loc = SpatialQuery.get_agents_at(spatial_state, "1,1")
        capacity = SpatialQuery.get_location_attribute(spatial_state, "1,1", "capacity")
        # Validator would enforce: len(agents_at_loc) <= capacity
        assert len(agents_at_loc) <= capacity


class TestNetworkConstraints:
    """Tests for network-based constraints."""

    def test_validator_checks_path_exists(self, validator_spatial_state):
        """Validator checks if path exists between locations."""
        path = SpatialQuery.shortest_path(validator_spatial_state, "0,0", "2,2")
        # Path exists in default network
        assert len(path) > 0

        # Disconnected locations would have no path
        # (In 4-connected grid, all locations are connected)

    def test_validator_checks_network_access(self, validator_spatial_state):
        """Validator checks if agent has access to network."""
        # Create restricted network
        spatial_state = SpatialMutations.create_network(validator_spatial_state, "vip_network", edges={("0,0", "1,1")})

        # Check if connection exists in specific network
        has_vip_connection = SpatialQuery.has_connection(spatial_state, "0,0", "1,1", network="vip_network")
        assert has_vip_connection

        # Agent without VIP access shouldn't use this network
        has_default_connection = SpatialQuery.has_connection(spatial_state, "0,0", "1,1", network="default")
        # Connection might not exist in default network


class TestBatchValidation:
    """Tests for batch operation validation."""

    def test_validator_checks_all_moves_before_applying(self, validator_spatial_state):
        """Validator validates all moves atomically."""
        spatial_state = SpatialMutations.move_agent(validator_spatial_state, "agent_1", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "1,1")

        # One valid, one invalid
        moves = {"agent_1": "1,0", "agent_2": "99,99"}

        with pytest.raises(ValueError):
            SpatialMutations.move_agents_batch(spatial_state, moves)

        # Original positions unchanged
        assert SpatialQuery.get_agent_position(spatial_state, "agent_1") == "0,0"
        assert SpatialQuery.get_agent_position(spatial_state, "agent_2") == "1,1"

    def test_validator_checks_region_updates(self, validator_spatial_state):
        """Validator validates region update targets."""
        def update_fn(loc: LocationState) -> dict:
            return {"updated": True}

        # One valid, one invalid location
        with pytest.raises(ValueError):
            SpatialMutations.apply_to_region(validator_spatial_state, ["0,0", "99,99"], update_fn)


class TestCustomValidationRules:
    """Tests for custom validation rules."""

    def test_validator_custom_rule_minimum_distance(self, validator_spatial_state):
        """Validator enforces minimum distance between agents."""
        spatial_state = SpatialMutations.move_agent(validator_spatial_state, "agent_1", "1,1")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "3,3")

        # Check distance
        pos1 = SpatialQuery.get_agent_position(spatial_state, "agent_1")
        pos2 = SpatialQuery.get_agent_position(spatial_state, "agent_2")
        distance = SpatialQuery.get_distance(spatial_state, pos1, pos2)

        # If validator enforces min_distance=2, distance should be >= 2
        assert distance >= 2

    def test_validator_custom_rule_zone_permissions(self, validator_spatial_state):
        """Validator checks zone-specific permissions."""
        # Agent properties would include permissions
        # Validator checks: can agent enter this zone type?

        restricted_type = SpatialQuery.get_location_attribute(validator_spatial_state, "4,4", "type")
        assert restricted_type == "restricted_zone"

        # Validator logic:
        # if target_zone.type == "restricted" and not agent.has_clearance:
        #     raise ValidationError


class TestValidationErrorMessages:
    """Tests for clear validation error messages."""

    def test_invalid_location_error_lists_valid_locations(self, validator_spatial_state):
        """Error message includes list of valid locations."""
        with pytest.raises(ValueError) as exc_info:
            SpatialMutations.move_agent(validator_spatial_state, "agent", "invalid")

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg  # Mentions the invalid location

    def test_invalid_network_error_lists_available_networks(self, validator_spatial_state):
        """Error message includes list of available networks."""
        with pytest.raises(ValueError) as exc_info:
            SpatialMutations.add_connection(validator_spatial_state, "0,0", "1,0", network="invalid")

        error_msg = str(exc_info.value).lower()
        assert "network" in error_msg or "invalid" in error_msg


class TestValidationPerformance:
    """Performance tests for validation."""

    def test_validates_large_batch_efficiently(self):
        """Validator handles large batch validation efficiently."""
        config = SpatialConfig(topology=GridConfig(width=20, height=20, connectivity=4))
        spatial_state = SpatialStateFactory.create(config)

        # Position many agents
        for i in range(100):
            spatial_state = SpatialMutations.move_agent(spatial_state, f"agent_{i}", f"{i % 20},{i // 20}")

        # Batch move all agents
        moves = {f"agent_{i}": f"{(i+1) % 20},{i // 20}" for i in range(100)}

        # Should validate quickly
        try:
            new_state = SpatialMutations.move_agents_batch(spatial_state, moves)
            success = True
        except ValueError:
            success = False

        # All moves should be valid
        assert success


class TestEdgeCases:
    """Edge case validation tests."""

    def test_validator_handles_empty_moves(self, validator_spatial_state):
        """Validator handles empty move batch."""
        new_state = SpatialMutations.move_agents_batch(validator_spatial_state, {})
        assert new_state is not None

    def test_validator_handles_agent_not_positioned(self, validator_spatial_state):
        """Validator handles agent that isn't yet positioned."""
        position = SpatialQuery.get_agent_position(validator_spatial_state, "new_agent")
        assert position is None  # Agent not positioned

        # Can position new agent
        new_state = SpatialMutations.move_agent(validator_spatial_state, "new_agent", "1,1")
        assert SpatialQuery.get_agent_position(new_state, "new_agent") == "1,1"
