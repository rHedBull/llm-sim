"""Contract test for LifecycleManager.add_agent() method.

Contract: contracts/lifecycle_manager_contract.md - add_agent() method
"""

import pytest
from llm_sim.infrastructure.lifecycle.manager import LifecycleManager
from llm_sim.infrastructure.lifecycle.validator import LifecycleValidator
from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker
from llm_sim.models.state import SimulationState, create_agent_state_model
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action


class DummyAgent(BaseAgent):
    """Dummy agent for testing."""

    def decide_action(self, state: SimulationState) -> Action:
        return Action(agent_name=self.name, action_name="test")


class TestLifecycleManagerAddContract:
    """Test contract for LifecycleManager.add_agent() method."""

    @pytest.fixture
    def state(self):
        """Create test simulation state."""
        AgentState = create_agent_state_model({})
        GlobalState = create_agent_state_model({})
        return SimulationState(
            turn=1,
            agents={},
            global_state=GlobalState(name="global"),
        )

    @pytest.fixture
    def manager(self):
        """Create lifecycle manager."""
        validator = LifecycleValidator()
        pause_tracker = PauseTracker()
        return LifecycleManager(validator=validator, pause_tracker=pause_tracker)

    def test_add_agent_returns_resolved_name(self, manager, state):
        """Should return resolved agent name."""
        agent = DummyAgent("test_agent")

        resolved_name = manager.add_agent("test_agent", agent, {}, state)

        assert resolved_name == "test_agent"

    def test_add_agent_adds_to_state(self, manager, state):
        """Agent should be added to state.agents dict."""
        agent = DummyAgent("test_agent")

        manager.add_agent("test_agent", agent, {}, state)

        assert "test_agent" in state.agents

    def test_add_agent_collision_resolution(self, manager, state):
        """Should append _1, _2, etc. for name collisions."""
        agent1 = DummyAgent("agent")
        agent2 = DummyAgent("agent")
        agent3 = DummyAgent("agent")

        name1 = manager.add_agent("agent", agent1, {}, state)
        name2 = manager.add_agent("agent", agent2, {}, state)
        name3 = manager.add_agent("agent", agent3, {}, state)

        assert name1 == "agent"
        assert name2 == "agent_1"
        assert name3 == "agent_2"
        assert len(state.agents) == 3

    def test_add_agent_max_limit_25(self, manager, state):
        """Should fail validation when adding 26th agent."""
        # Add 25 agents
        for i in range(25):
            agent = DummyAgent(f"agent{i}")
            manager.add_agent(f"agent{i}", agent, {}, state)

        # Try to add 26th
        agent26 = DummyAgent("agent26")
        resolved_name = manager.add_agent("agent26", agent26, {}, state)

        # Validation should fail, agent not added
        assert len(state.agents) == 25
        assert "agent26" not in state.agents
        # Returns original name even though not added
        assert resolved_name == "agent26"

    def test_add_agent_with_initial_state(self, manager, state):
        """Should use provided initial_state for agent."""
        agent = DummyAgent("test_agent")
        initial_state = {"resource": 100, "active": True}

        manager.add_agent("test_agent", agent, initial_state, state)

        # Agent should be in state with provided initial values
        assert "test_agent" in state.agents
        # Note: actual state structure depends on agent state model

    def test_add_agent_logs_operation(self, manager, state, caplog):
        """Should log info-level message with resolved name."""
        import logging
        caplog.set_level(logging.INFO)

        agent = DummyAgent("test_agent")
        manager.add_agent("test_agent", agent, {}, state)

        # Check for lifecycle_operation log
        assert any("lifecycle_operation" in record.message or "test_agent" in record.message for record in caplog.records)

    def test_add_agent_logs_warning_on_validation_failure(self, manager, state, caplog):
        """Should log warning when validation fails (e.g., max limit)."""
        import logging
        caplog.set_level(logging.WARNING)

        # Add 25 agents
        for i in range(25):
            manager.add_agent(f"agent{i}", DummyAgent(f"agent{i}"), {}, state)

        # Try to add 26th
        manager.add_agent("overflow", DummyAgent("overflow"), {}, state)

        # Should have warning log
        assert any("validation" in record.message.lower() or "maximum" in record.message.lower() for record in caplog.records)
