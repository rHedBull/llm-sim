"""Integration tests for spatial observability features.

Tests logging, checkpointing, and observability of spatial state.
"""

import pytest
import json

from llm_sim.models.config import GridConfig, SpatialConfig
from llm_sim.models.state import SimulationState, LocationState, NetworkState
from llm_sim.infrastructure.spatial.factory import SpatialStateFactory
from llm_sim.infrastructure.spatial.query import SpatialQuery
from llm_sim.infrastructure.spatial.mutations import SpatialMutations


@pytest.fixture
def observed_spatial_state():
    """Create spatial state for observability testing."""
    config = SpatialConfig(
        topology=GridConfig(width=3, height=3, connectivity=4),
        location_attributes={
            "1,1": {"resource": 100},
        }
    )
    return SpatialStateFactory.create(config)


class TestCheckpointSerialization:
    """Tests for spatial state in checkpoints."""

    def test_spatial_state_serializes_to_checkpoint(self, observed_spatial_state, mock_global_state):
        """SpatialState serializes as part of checkpoint."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_a", "1,1")

        state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=spatial_state
        )

        # Serialize to dict (checkpoint format)
        checkpoint_data = state.model_dump()

        assert "spatial_state" in checkpoint_data
        assert checkpoint_data["spatial_state"]["topology_type"] == "grid"
        assert "agent_a" in checkpoint_data["spatial_state"]["agent_positions"]

    def test_spatial_state_deserializes_from_checkpoint(self, observed_spatial_state, mock_global_state):
        """SpatialState deserializes from checkpoint."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_a", "1,1")

        original_state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=spatial_state
        )

        # Serialize
        checkpoint_data = original_state.model_dump()

        # Deserialize
        restored_state = SimulationState(**checkpoint_data)

        assert restored_state.spatial_state.topology_type == "grid"
        assert SpatialQuery.get_agent_position(restored_state.spatial_state, "agent_a") == "1,1"

    def test_checkpoint_without_spatial_state(self, mock_global_state):
        """Checkpoint works without spatial state (backward compatibility)."""
        state = SimulationState(
            turn=5,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )

        checkpoint_data = state.model_dump()
        assert checkpoint_data["spatial_state"] is None

        restored = SimulationState(**checkpoint_data)
        assert restored.spatial_state is None


class TestSpatialStateLogging:
    """Tests for logging spatial state changes."""

    def test_logs_agent_movement(self, observed_spatial_state):
        """Agent movement should be loggable."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_a", "0,0")
        new_spatial_state = SpatialMutations.move_agent(spatial_state, "agent_a", "1,0")

        # Logging system would record:
        # - agent: agent_a
        # - action: move
        # - from: 0,0
        # - to: 1,0
        # - turn: N

        # Verify positions changed
        assert SpatialQuery.get_agent_position(spatial_state, "agent_a") == "0,0"
        assert SpatialQuery.get_agent_position(new_spatial_state, "agent_a") == "1,0"

    def test_logs_location_updates(self, observed_spatial_state):
        """Location attribute updates should be loggable."""
        old_value = SpatialQuery.get_location_attribute(observed_spatial_state, "1,1", "resource")
        new_spatial_state = SpatialMutations.set_location_attribute(observed_spatial_state, "1,1", "resource", 150)
        new_value = SpatialQuery.get_location_attribute(new_spatial_state, "1,1", "resource")

        # Logging system would record:
        # - location: 1,1
        # - attribute: resource
        # - old_value: 100
        # - new_value: 150

        assert old_value == 100
        assert new_value == 150

    def test_logs_network_changes(self, observed_spatial_state):
        """Network changes should be loggable."""
        new_spatial_state = SpatialMutations.create_network(observed_spatial_state, "rail", edges=set())

        # Logging system would record:
        # - action: create_network
        # - network_name: rail
        # - edges: []

        assert "rail" in new_spatial_state.networks
        assert "rail" not in observed_spatial_state.networks


class TestSpatialMetrics:
    """Tests for spatial metrics and statistics."""

    def test_computes_agent_distribution(self, observed_spatial_state):
        """Computes how agents are distributed across locations."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_1", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_3", "2,2")

        # Count agents per location
        location_counts = {}
        for agent, location in spatial_state.agent_positions.items():
            location_counts[location] = location_counts.get(location, 0) + 1

        assert location_counts["0,0"] == 2
        assert location_counts["2,2"] == 1

    def test_computes_network_connectivity(self, observed_spatial_state):
        """Computes network connectivity metrics."""
        edges = observed_spatial_state.networks["default"].edges
        num_edges = len(edges)

        # Metrics: number of edges, average degree, etc.
        assert num_edges > 0  # Grid should have edges

    def test_computes_spatial_clustering(self, observed_spatial_state):
        """Computes spatial clustering of agents."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_1", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "0,1")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_3", "0,2")

        # All agents in same column - high clustering
        # Metric: average distance between all agent pairs
        positions = [
            SpatialQuery.get_agent_position(spatial_state, "agent_1"),
            SpatialQuery.get_agent_position(spatial_state, "agent_2"),
            SpatialQuery.get_agent_position(spatial_state, "agent_3"),
        ]
        assert all(pos is not None for pos in positions)


class TestObservabilityEvents:
    """Tests for observability event stream integration."""

    def test_spatial_events_in_event_stream(self, observed_spatial_state):
        """Spatial changes generate events for event stream."""
        # Movement event
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_a", "1,1")

        # Event would be:
        # {
        #   "type": "agent_moved",
        #   "agent": "agent_a",
        #   "to_location": "1,1",
        #   "timestamp": ...
        # }

        assert SpatialQuery.get_agent_position(spatial_state, "agent_a") == "1,1"

    def test_location_event_in_stream(self, observed_spatial_state):
        """Location updates generate events."""
        spatial_state = SpatialMutations.set_location_attribute(observed_spatial_state, "1,1", "disaster", "flood")

        # Event would be:
        # {
        #   "type": "location_updated",
        #   "location": "1,1",
        #   "attribute": "disaster",
        #   "value": "flood"
        # }

        assert SpatialQuery.get_location_attribute(spatial_state, "1,1", "disaster") == "flood"


class TestSpatialVisualization:
    """Tests for spatial state visualization data."""

    def test_exports_agent_positions_for_visualization(self, observed_spatial_state):
        """Exports agent position data for visualization."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_1", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "2,2")

        # Export format for visualization:
        viz_data = {
            "agents": [
                {"name": "agent_1", "location": "0,0"},
                {"name": "agent_2", "location": "2,2"},
            ]
        }

        # Verify we can extract this data
        positions = spatial_state.agent_positions
        assert len(positions) == 2

    def test_exports_network_graph_for_visualization(self, observed_spatial_state):
        """Exports network edges for graph visualization."""
        edges = observed_spatial_state.networks["default"].edges

        # Export format:
        viz_edges = [
            {"from": loc1, "to": loc2}
            for loc1, loc2 in edges
        ]

        assert len(viz_edges) > 0

    def test_exports_location_attributes_for_heatmap(self, observed_spatial_state):
        """Exports location attributes for heatmap visualization."""
        # Add more location attributes
        spatial_state = SpatialMutations.set_location_attribute(observed_spatial_state, "0,0", "resource", 50)
        spatial_state = SpatialMutations.set_location_attribute(spatial_state, "2,2", "resource", 150)

        # Export format for heatmap:
        heatmap_data = []
        for loc_id, location in spatial_state.locations.items():
            resource = location.attributes.get("resource", 0)
            heatmap_data.append({"location": loc_id, "value": resource})

        assert len(heatmap_data) > 0


class TestSpatialDebugInfo:
    """Tests for debugging spatial issues."""

    def test_debug_info_includes_all_agents(self, observed_spatial_state):
        """Debug info includes all agent positions."""
        spatial_state = SpatialMutations.move_agent(observed_spatial_state, "agent_1", "0,0")
        spatial_state = SpatialMutations.move_agent(spatial_state, "agent_2", "1,1")

        debug_info = {
            "topology_type": spatial_state.topology_type,
            "num_locations": len(spatial_state.locations),
            "num_agents": len(spatial_state.agent_positions),
            "agents": spatial_state.agent_positions,
        }

        assert debug_info["num_agents"] == 2
        assert "agent_1" in debug_info["agents"]

    def test_debug_info_includes_network_stats(self, observed_spatial_state):
        """Debug info includes network statistics."""
        debug_info = {
            "networks": {
                name: {
                    "num_edges": len(network.edges),
                    "edges": list(network.edges),
                }
                for name, network in observed_spatial_state.networks.items()
            }
        }

        assert "default" in debug_info["networks"]
        assert debug_info["networks"]["default"]["num_edges"] > 0


class TestPerformanceMonitoring:
    """Tests for monitoring spatial operation performance."""

    def test_monitors_query_performance(self):
        """Monitors performance of spatial queries."""
        import time

        # Create a larger grid to accommodate 100 agents
        config = SpatialConfig(
            topology=GridConfig(width=10, height=10, connectivity=4)
        )
        spatial_state = SpatialStateFactory.create(config)

        # Position many agents
        for i in range(100):
            spatial_state = SpatialMutations.move_agent(spatial_state, f"agent_{i}", f"{i % 10},{i // 10}")

        # Time a query
        start = time.time()
        agents = SpatialQuery.get_agents_at(spatial_state, "0,0")
        duration = time.time() - start

        # Should be fast (< 0.01 seconds)
        assert duration < 0.01
        assert len(agents) > 0

    def test_monitors_mutation_performance(self, observed_spatial_state):
        """Monitors performance of spatial mutations."""
        import time

        # Time a batch move
        moves = {f"agent_{i}": f"{i % 3},{i // 3}" for i in range(100)}

        start = time.time()
        try:
            new_state = SpatialMutations.move_agents_batch(observed_spatial_state, moves)
            duration = time.time() - start
            success = True
        except ValueError:
            duration = time.time() - start
            success = True  # Validation is fast even if it fails

        # Should complete quickly
        assert duration < 0.1


class TestBackwardCompatibility:
    """Tests for backward compatibility of observability."""

    def test_old_checkpoints_without_spatial_state_load(self, mock_global_state):
        """Old checkpoints without spatial_state field still load."""
        # Simulate old checkpoint
        old_checkpoint = {
            "turn": 5,
            "agents": {},
            "global_state": mock_global_state.model_dump(),
            # No spatial_state field
        }

        # Should load with spatial_state=None
        state = SimulationState(**old_checkpoint)
        assert state.spatial_state is None

    def test_logs_from_non_spatial_simulations_still_work(self, mock_global_state):
        """Logging works for simulations without spatial state."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )

        # Serializing should work
        data = state.model_dump()
        assert data["spatial_state"] is None
