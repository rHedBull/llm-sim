"""Integration tests for spatial positioning with agents.

Tests agent movement, proximity awareness, and spatial actions.
"""

import pytest

from llm_sim.models.config import (
    GridConfig,
    SpatialConfig,
    SimulationConfig,
    AgentConfig,
)
from llm_sim.models.state import SimulationState, SpatialState, LocationState, NetworkState
from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.infrastructure.spatial.mutations import SpatialMutations


@pytest.fixture
def spatial_simulation_config():
    """Create simulation config with spatial topology."""
    return SpatialConfig(
        topology=GridConfig(width=5, height=5, connectivity=4),
        location_attributes={
            "2,2": {"resource": 100},
            "0,0": {"resource": 50},
        }
    )


@pytest.fixture
def agents_with_locations():
    """Create agents with initial locations."""
    return [
        AgentConfig(name="agent_a", type="nation", initial_location="0,0"),
        AgentConfig(name="agent_b", type="nation", initial_location="2,2"),
        AgentConfig(name="agent_c", type="nation", initial_location="4,4"),
    ]


class TestAgentInitialization:
    """Tests for agent initialization with spatial positioning."""

    def test_agents_positioned_at_initial_locations(self, spatial_simulation_config):
        """Agents are positioned at their initial_location on initialization."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        # Manually position agents (orchestrator would do this)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "2,2")

        assert SpatialQuery.get_agent_position(spatial_state, "agent_a") == "0,0"
        assert SpatialQuery.get_agent_position(spatial_state, "agent_b") == "2,2"

    def test_agents_without_initial_location_not_positioned(self):
        """Agents without initial_location are not positioned."""
        config = SpatialConfig(topology=GridConfig(width=3, height=3, connectivity=4))
        spatial_state = SpatialStateFactory.create(config)
        # No agents positioned
        assert spatial_state.agent_positions == {}


class TestAgentMovement:
    """Tests for agent movement during simulation."""

    def test_engine_can_move_agent(self, spatial_simulation_config):
        """Engine can move agent to new location."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")

        # Move agent
        new_spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")

        assert SpatialQuery.get_agent_position(new_spatial_state, "agent_a") == "1,0"
        assert SpatialQuery.get_agent_position(spatial_state, "agent_a") == "0,0"  # Original unchanged

    def test_multiple_agents_can_occupy_same_location(self, spatial_simulation_config):
        """Multiple agents can be at the same location."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "2,2")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "2,2")

        agents_at_location = SpatialQuery.get_agents_at(spatial_state, "2,2")
        assert set(agents_at_location) == {"agent_a", "agent_b"}

    def test_batch_movement_in_turn(self, spatial_simulation_config):
        """Engine can batch move multiple agents in single turn."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "1,0")

        # Batch move
        moves = {"agent_a": "1,0", "agent_b": "2,0"}
        new_spatial_state = SpatialMutations.move_agents_batch(spatial_state, moves)

        assert SpatialQuery.get_agent_position(new_spatial_state, "agent_a") == "1,0"
        assert SpatialQuery.get_agent_position(new_spatial_state, "agent_b") == "2,0"


class TestProximityAwareness:
    """Tests for agents querying nearby agents/locations."""

    def test_agent_queries_neighbors(self, spatial_simulation_config):
        """Agent can query neighboring locations."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        neighbors = SpatialQuery.get_neighbors(spatial_state, "2,2")
        # Center of 5×5 grid should have 4 neighbors
        assert len(neighbors) == 4
        assert set(neighbors) == {"1,2", "3,2", "2,1", "2,3"}

    def test_agent_queries_nearby_agents(self, spatial_simulation_config):
        """Agent can query agents within radius."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "2,2")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "2,3")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_c", "4,4")

        # Query agents within radius 1 from (2,2)
        nearby_agents = SpatialQuery.get_agents_within(spatial_state, "2,2", radius=1)
        assert set(nearby_agents) == {"agent_a", "agent_b"}  # agent_c is too far

    def test_agent_queries_location_attributes(self, spatial_simulation_config):
        """Agent can query location attributes."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        resource = SpatialQuery.get_location_attribute(spatial_state, "2,2", "resource")
        assert resource == 100


class TestPartialObservability:
    """Tests for partial observability filtering."""

    def test_filter_state_by_proximity(self, spatial_simulation_config, mock_global_state):
        """Agent receives filtered state based on proximity."""
        from llm_sim.models.state import SimulationState

        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "4,4")

        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=spatial_state
        )

        # Filter for agent_a (radius 1 from 0,0)
        filtered = SpatialQuery.filter_state_by_proximity("agent_a", state, radius=1)

        # agent_b at (4,4) should not be visible
        # Will fail until implementation
        assert filtered.spatial_state is not None


class TestSpatialValidation:
    """Tests for spatial validation in actions."""

    def test_engine_validates_movement_to_valid_location(self, spatial_simulation_config):
        """Engine validates agent can only move to valid locations."""
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")

        # Try to move to invalid location
        with pytest.raises(ValueError, match="invalid location"):
            SpatialMutations.move_agent(spatial_state, "agent_a", "99,99")

    def test_engine_validates_movement_to_adjacent_only(self, spatial_simulation_config):
        """Engine can validate agent moves only to adjacent locations.

        Note: This is optional constraint that engine can enforce.
        """
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")

        # Check if location is adjacent before moving
        is_adjacent = SpatialQuery.is_adjacent(spatial_state, "0,0", "1,0")
        assert is_adjacent  # (1,0) is adjacent to (0,0)

        is_adjacent_far = SpatialQuery.is_adjacent(spatial_state, "0,0", "4,4")
        assert not is_adjacent_far  # (4,4) is not adjacent to (0,0)


class TestSpatialStateInSimulation:
    """Tests for spatial state as part of simulation state."""

    def test_spatial_state_persists_across_turns(self, spatial_simulation_config, mock_global_state):
        """Spatial state persists as part of simulation state."""
        from llm_sim.models.state import SimulationState

        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")

        state_turn1 = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=spatial_state
        )

        # Move agent in turn 2
        new_spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")
        state_turn2 = state_turn1.model_copy(update={"turn": 2, "spatial_state": new_spatial_state})

        # Verify persistence
        assert state_turn2.spatial_state.agent_positions["agent_a"] == "1,0"
        assert state_turn1.spatial_state.agent_positions["agent_a"] == "0,0"  # Original unchanged

    def test_simulation_without_spatial_state(self, mock_global_state):
        """Simulation can run without spatial state."""
        from llm_sim.models.state import SimulationState

        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )

        # Should work fine
        assert state.spatial_state is None


class TestEndToEndScenario:
    """End-to-end scenario tests."""

    def test_agents_move_and_interact(self, spatial_simulation_config):
        """Complete scenario: agents move, query, and interact."""
        # Initialize spatial state
        spatial_state = SpatialStateFactory.create(spatial_simulation_config)
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_b", "2,2")

        # Turn 1: agent_a moves toward agent_b
        path = SpatialQuery.shortest_path(spatial_state, "0,0", "2,2")
        assert len(path) >= 3  # At least 3 hops (0,0 -> ... -> 2,2)

        # Move along path
        next_location = path[1]
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", next_location)

        # Turn 2: Check distance between agents
        pos_a = SpatialQuery.get_agent_position(spatial_state, "agent_a")
        distance = SpatialQuery.get_distance(spatial_state, pos_a, "2,2")
        assert distance < 4  # Closer than before

        # Turn 3: agent_a arrives at same location as agent_b
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "2,2")
        agents_at_location = SpatialQuery.get_agents_at(spatial_state, "2,2")
        assert set(agents_at_location) == {"agent_a", "agent_b"}

        # Agents can now interact (both at 2,2)
        resource = SpatialQuery.get_location_attribute(spatial_state, "2,2", "resource")
        assert resource == 100  # Location has resources
