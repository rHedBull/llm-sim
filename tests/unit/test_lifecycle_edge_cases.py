"""Edge case tests for lifecycle operations."""

import pytest
from llm_sim.infrastructure.lifecycle.manager import LifecycleManager
from llm_sim.models.state import SimulationState, create_agent_state_model
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action


class DummyAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        return Action(agent_name=self.name, action_name="test")


@pytest.fixture
def state():
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
def manager():
    return LifecycleManager()


def test_pause_already_paused_agent(manager, state):
    """Validation should fail when pausing already-paused agent."""
    # Pause agent
    result1 = manager.pause_agent("agent1", None, state)
    assert result1 is True

    # Try to pause again
    result2 = manager.pause_agent("agent1", None, state)
    assert result2 is False
    assert "agent1" in state.paused_agents


def test_resume_non_paused_agent(manager, state):
    """Validation should fail when resuming non-paused agent."""
    result = manager.resume_agent("agent1", state)
    assert result is False


def test_last_agent_removal(manager):
    """Should allow removing last agent."""
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


def test_auto_resume_zero_turns_invalid(manager, state):
    """Auto-resume turns must be positive or None, not 0."""
    result = manager.pause_agent("agent1", 0, state)
    assert result is False
    assert "agent1" not in state.paused_agents


def test_auto_resume_negative_turns_invalid(manager, state):
    """Auto-resume turns must be positive or None, not negative."""
    result = manager.pause_agent("agent1", -1, state)
    assert result is False
    assert "agent1" not in state.paused_agents
