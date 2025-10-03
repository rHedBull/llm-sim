"""Edge case test: Max agent limit (25)."""

import pytest
from llm_sim.infrastructure.lifecycle.manager import LifecycleManager
from llm_sim.models.state import SimulationState, create_agent_state_model
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action


class DummyAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        return Action(agent_name=self.name, action_name="test")


def test_max_agent_limit_validation():
    """Validation should fail when adding 26th agent."""
    AgentState = create_agent_state_model({})
    GlobalState = create_agent_state_model({})
    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(name="global"),
    )

    manager = LifecycleManager()

    # Add 25 agents
    for i in range(25):
        result = manager.add_agent(f"agent{i}", DummyAgent(f"agent{i}"), {}, state)
        assert result == f"agent{i}"

    assert len(state.agents) == 25

    # Try to add 26th agent
    result = manager.add_agent("agent26", DummyAgent("agent26"), {}, state)

    # Should not be added (validation fails)
    assert len(state.agents) == 25
    assert "agent26" not in state.agents
