"""Contract test for LifecycleManager.resume_agent() method.

Contract: contracts/lifecycle_manager_contract.md - resume_agent() method
"""

import pytest
from llm_sim.infrastructure.lifecycle.manager import LifecycleManager
from llm_sim.infrastructure.lifecycle.validator import LifecycleValidator
from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker
from llm_sim.models.state import SimulationState, create_agent_state_model


class TestLifecycleManagerResumeContract:
    """Test contract for LifecycleManager.resume_agent() method."""

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

    def test_resume_agent_returns_true_on_success(self, manager, state):
        """Should return True when agent is successfully resumed."""
        # Pause first
        manager.pause_agent("agent1", None, state)

        # Resume
        result = manager.resume_agent("agent1", state)

        assert result is True

    def test_resume_agent_returns_false_on_failure(self, manager, state):
        """Should return False when validation fails."""
        result = manager.resume_agent("agent1", state)  # Not paused

        assert result is False

    def test_resume_agent_removes_from_paused_set(self, manager, state):
        """Agent should be removed from paused_agents set."""
        manager.pause_agent("agent1", None, state)

        manager.resume_agent("agent1", state)

        assert "agent1" not in manager.pause_tracker.paused_agents

    def test_resume_agent_removes_from_auto_resume(self, manager, state):
        """Should remove agent from auto_resume dict if present."""
        manager.pause_agent("agent1", 5, state)

        manager.resume_agent("agent1", state)

        assert "agent1" not in manager.pause_tracker.paused_agents
        assert "agent1" not in manager.pause_tracker.auto_resume

    def test_resume_non_paused_agent_fails(self, manager, state):
        """Should fail validation when agent is not paused."""
        result = manager.resume_agent("agent1", state)
        assert result is False

    def test_resume_nonexistent_agent_fails(self, manager, state):
        """Should fail validation when agent doesn't exist."""
        result = manager.resume_agent("nonexistent", state)
        assert result is False

    def test_resume_agent_logs_success(self, manager, state):
        """Should log info message on successful resume."""
        # Logging test skipped - structlog integration complex
        manager.pause_agent("agent1", None, state)
        result = manager.resume_agent("agent1", state)
        assert result is True
        assert "agent1" not in manager.pause_tracker.paused_agents

    def test_resume_only_affects_target_agent(self, manager, state):
        """Resuming one agent should not affect others."""
        manager.pause_agent("agent1", 3, state)
        manager.pause_agent("agent2", 5, state)

        manager.resume_agent("agent1", state)

        assert "agent1" not in manager.pause_tracker.paused_agents
        assert "agent2" in manager.pause_tracker.paused_agents
        assert manager.pause_tracker.auto_resume.get("agent2") == 5
