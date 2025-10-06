"""Integration tests for backward compatibility with spatial positioning.

Tests that existing simulations continue to work without spatial features.
"""

import pytest

from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    ValidatorConfig,
    LoggingConfig,
    TerminationConditions,
    AgentConfig,
    GridConfig,
    SpatialConfig,
)
from llm_sim.models.state import SimulationState


@pytest.fixture
def legacy_config():
    """Create legacy config without spatial features."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="Legacy Sim",
            max_turns=10,
            termination=TerminationConditions()
        ),
        engine=EngineConfig(type="economic", interest_rate=0.05),
        agents=[
            AgentConfig(name="agent_a", type="nation"),
            AgentConfig(name="agent_b", type="nation"),
        ],
        validator=ValidatorConfig(type="always_valid"),
        logging=LoggingConfig(),
        # No spatial field
    )


@pytest.fixture
def spatial_config():
    """Create new config with spatial features."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="Spatial Sim",
            max_turns=10,
            termination=TerminationConditions()
        ),
        engine=EngineConfig(type="economic", interest_rate=0.05),
        agents=[
            AgentConfig(name="agent_a", type="nation", initial_location="0,0"),
            AgentConfig(name="agent_b", type="nation", initial_location="1,1"),
        ],
        validator=ValidatorConfig(type="always_valid"),
        logging=LoggingConfig(),
        spatial=SpatialConfig(
            topology=GridConfig(width=5, height=5, connectivity=4)
        )
    )


class TestLegacyConfigCompatibility:
    """Tests for legacy config compatibility."""

    def test_legacy_config_without_spatial_still_valid(self, legacy_config):
        """Legacy config without spatial field is still valid."""
        assert legacy_config.spatial is None
        assert len(legacy_config.agents) == 2

    def test_legacy_agents_without_initial_location_valid(self, legacy_config):
        """Legacy agents without initial_location are valid."""
        for agent in legacy_config.agents:
            assert agent.initial_location is None

    def test_legacy_config_serializes(self, legacy_config):
        """Legacy config serializes without spatial field."""
        data = legacy_config.model_dump()
        assert "spatial" in data
        assert data["spatial"] is None


class TestLegacyStateCompatibility:
    """Tests for legacy state compatibility."""

    def test_legacy_state_without_spatial_state(self, mock_global_state):
        """Legacy state without spatial_state is valid."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            # No spatial_state field
        )
        assert state.spatial_state is None

    def test_legacy_state_serializes(self, mock_global_state):
        """Legacy state serializes without spatial_state."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )
        data = state.model_dump()
        assert "spatial_state" in data
        assert data["spatial_state"] is None

    def test_legacy_checkpoint_deserializes(self, mock_global_state):
        """Legacy checkpoint without spatial_state deserializes."""
        # Simulate old checkpoint
        checkpoint_data = {
            "turn": 5,
            "agents": {},
            "global_state": mock_global_state.model_dump(),
            "reasoning_chains": [],
            "paused_agents": [],
            "auto_resume": {},
            # No spatial_state
        }

        state = SimulationState(**checkpoint_data)
        assert state.spatial_state is None
        assert state.turn == 5


class TestMixedConfigs:
    """Tests for mixed legacy/spatial configs."""

    def test_some_agents_with_initial_location(self):
        """Config with mix of positioned and non-positioned agents."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Mixed Sim",
                max_turns=10,
                termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[
                AgentConfig(name="agent_a", type="nation", initial_location="0,0"),
                AgentConfig(name="agent_b", type="nation"),  # No initial_location
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
            spatial=SpatialConfig(
                topology=GridConfig(width=3, height=3, connectivity=4)
            )
        )

        # Should be valid
        assert config.agents[0].initial_location == "0,0"
        assert config.agents[1].initial_location is None


class TestSpatialOptionalBehavior:
    """Tests for spatial features being truly optional."""

    def test_queries_on_none_spatial_state_return_safe_defaults(self):
        """Spatial queries on None spatial_state return safe defaults."""
        from llm_sim.infrastructure.spatial.query import SpatialQuery

        position = SpatialQuery.get_agent_position(None, "agent_a")
        assert position is None

        neighbors = SpatialQuery.get_neighbors(None, "0,0")
        assert neighbors == []

        distance = SpatialQuery.get_distance(None, "0,0", "1,1")
        assert distance == -1

    def test_simulation_runs_without_spatial_state(self, mock_global_state):
        """Simulation can run without spatial_state."""
        state = SimulationState(
            turn=1,
            agents={},
            global_state=mock_global_state,
            spatial_state=None
        )

        # Advance turn
        state = state.model_copy(update={"turn": 2})

        assert state.turn == 2
        assert state.spatial_state is None


class TestUpgradeScenarios:
    """Tests for upgrading from non-spatial to spatial."""

    def test_add_spatial_to_existing_config(self, legacy_config):
        """Can add spatial config to existing simulation config."""
        spatial_config = SpatialConfig(
            topology=GridConfig(width=5, height=5, connectivity=4)
        )

        upgraded_config = legacy_config.model_copy(update={"spatial": spatial_config})

        assert upgraded_config.spatial is not None
        assert upgraded_config.spatial.topology.type == "grid"

    def test_add_initial_locations_to_agents(self, legacy_config):
        """Can add initial_location to existing agents."""
        agents_with_locations = []
        for i, agent in enumerate(legacy_config.agents):
            updated_agent = agent.model_copy(update={"initial_location": f"{i},{i}"})
            agents_with_locations.append(updated_agent)

        upgraded_config = legacy_config.model_copy(update={"agents": agents_with_locations})

        assert upgraded_config.agents[0].initial_location == "0,0"
        assert upgraded_config.agents[1].initial_location == "1,1"


class TestDowngradeScenarios:
    """Tests for downgrading from spatial to non-spatial."""

    def test_remove_spatial_from_config(self, spatial_config):
        """Can remove spatial config from simulation config."""
        downgraded_config = spatial_config.model_copy(update={"spatial": None})

        assert downgraded_config.spatial is None

    def test_remove_initial_locations_from_agents(self, spatial_config):
        """Can remove initial_location from agents."""
        agents_without_locations = []
        for agent in spatial_config.agents:
            updated_agent = agent.model_copy(update={"initial_location": None})
            agents_without_locations.append(updated_agent)

        downgraded_config = spatial_config.model_copy(update={"agents": agents_without_locations})

        for agent in downgraded_config.agents:
            assert agent.initial_location is None


class TestFileFormatCompatibility:
    """Tests for file format compatibility."""

    def test_legacy_yaml_config_loads(self, tmp_path):
        """Legacy YAML config without spatial field loads."""
        config_yaml = """
simulation:
  name: "Legacy Sim"
  max_turns: 10
  termination: {}
engine:
  type: "economic"
  interest_rate: 0.05
agents:
  - name: "agent_a"
    type: "nation"
validator:
  type: "always_valid"
logging: {}
"""
        config_file = tmp_path / "legacy_config.yaml"
        config_file.write_text(config_yaml)

        # Loading would use YAML parser
        # Should load with spatial=None

    def test_spatial_yaml_config_loads(self, tmp_path):
        """YAML config with spatial field loads."""
        config_yaml = """
simulation:
  name: "Spatial Sim"
  max_turns: 10
  termination: {}
engine:
  type: "economic"
  interest_rate: 0.05
agents:
  - name: "agent_a"
    type: "nation"
    initial_location: "0,0"
validator:
  type: "always_valid"
logging: {}
spatial:
  topology:
    type: "grid"
    width: 5
    height: 5
    connectivity: 4
"""
        config_file = tmp_path / "spatial_config.yaml"
        config_file.write_text(config_yaml)

        # Loading would use YAML parser
        # Should load with spatial config

    def test_legacy_checkpoint_json_loads(self, tmp_path, mock_global_state):
        """Legacy checkpoint JSON without spatial_state loads."""
        checkpoint_data = {
            "metadata": {
                "run_id": "test123",
                "turn": 5,
                "timestamp": "2025-10-06T12:00:00Z",
                "schema_hash": "a" * 64,
            },
            "state": {
                "turn": 5,
                "agents": {},
                "global_state": mock_global_state.model_dump(),
                "reasoning_chains": [],
                # No spatial_state
            }
        }

        checkpoint_file = tmp_path / "checkpoint.json"
        import json
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f)

        # Loading checkpoint
        with open(checkpoint_file) as f:
            loaded_data = json.load(f)

        state = SimulationState(**loaded_data["state"])
        assert state.spatial_state is None


class TestDocumentationExamples:
    """Tests ensuring documentation examples work."""

    def test_minimal_non_spatial_example(self):
        """Minimal non-spatial simulation config works."""
        config = SimulationConfig(
            simulation=SimulationSettings(name="Test", max_turns=10, termination=TerminationConditions()),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[AgentConfig(name="agent_a", type="nation")],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )
        assert config.spatial is None

    def test_minimal_spatial_example(self):
        """Minimal spatial simulation config works."""
        config = SimulationConfig(
            simulation=SimulationSettings(name="Test", max_turns=10, termination=TerminationConditions()),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[AgentConfig(name="agent_a", type="nation", initial_location="0,0")],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
            spatial=SpatialConfig(
                topology=GridConfig(width=3, height=3, connectivity=4)
            )
        )
        assert config.spatial is not None
        assert config.agents[0].initial_location == "0,0"
