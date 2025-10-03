"""Contract test for LifecycleManager.remove_agent() method.

Contract: contracts/lifecycle_manager_contract.md - remove_agent() method
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


class TestLifecycleManagerRemoveContract:
    """Test contract for LifecycleManager.remove_agent() method."""

    @pytest.fixture
    def state(self):
        """Create test simulation state with agents."""
        AgentState = create_agent_state_model({})
        GlobalState = create_agent_state_model({})
        return SimulationState(
            turn=1,
            agents={
                "agent1": AgentState(name="agent1"),
                "agent2": AgentState(name="agent2"),
            },
            global_state=GlobalState(name="global"),
        )

    @pytest.fixture
    def manager(self):
        """Create lifecycle manager."""
        validator = LifecycleValidator()
        pause_tracker = PauseTracker()
        return LifecycleManager(validator=validator, pause_tracker=pause_tracker)

    def test_remove_agent_returns_true_on_success(self, manager, state):
        """Should return True when agent is successfully removed."""
        result = manager.remove_agent("agent1", state)

        assert result is True

    def test_remove_agent_returns_false_on_failure(self, manager, state):
        """Should return False when agent doesn't exist."""
        result = manager.remove_agent("nonexistent", state)

        assert result is False

    def test_remove_agent_removes_from_state(self, manager, state):
        """Agent should be removed from state.agents dict."""
        manager.remove_agent("agent1", state)

        assert "agent1" not in state.agents
        assert "agent2" in state.agents

    def test_remove_agent_removes_from_paused_set(self, manager, state):
        """Should remove agent from paused_agents if paused."""
        # Pause agent first
        manager.pause_agent("agent1", None, state)

        # Remove agent
        manager.remove_agent("agent1", state)

        assert "agent1" not in state.agents
        assert "agent1" not in manager.pause_tracker.paused_agents

    def test_remove_agent_removes_from_auto_resume(self, manager, state):
        """Should remove agent from auto_resume dict if present."""
        # Pause agent with auto_resume
        manager.pause_agent("agent1", 5, state)

        # Remove agent
        manager.remove_agent("agent1", state)

        assert "agent1" not in state.agents
        assert "agent1" not in manager.pause_tracker.auto_resume

    def test_remove_nonexistent_agent_logs_warning(self, manager, state, caplog):
        """Should log warning when trying to remove nonexistent agent."""
        import logging
        caplog.set_level(logging.WARNING)

        manager.remove_agent("nonexistent", state)

        assert any("validation" in record.message.lower() or "nonexistent" in record.message.lower() for record in caplog.records)

    def test_remove_agent_logs_success(self, manager, state, caplog):
        """Should log info message on successful removal."""
        import logging
        caplog.set_level(logging.INFO)

        manager.remove_agent("agent1", state)

        assert any("lifecycle" in record.message.lower() or "agent1" in record.message for record in caplog.records)

    def test_remove_last_agent_allowed(self, manager):
        """Should allow removing last agent (simulation can have 0 agents)."""
        AgentState = create_agent_state_model({})
        GlobalState = create_agent_state_model({})
        state = SimulationState(
            turn=1,
            agents={"only_agent": AgentState(name="only_agent")},
            global_state=GlobalState(name="global"),
        )

        result = manager.remove_agent("only_agent", state)

        assert result is True
        assert len(state.agents) == 0
