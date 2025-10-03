"""Edge case test: Duplicate name collision resolution."""

import pytest
from llm_sim.infrastructure.lifecycle.manager import LifecycleManager
from llm_sim.models.state import SimulationState, create_agent_state_model
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action


class DummyAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        return Action(agent_name=self.name, action_name="test")


def test_name_collision_auto_rename():
    """Test agent → agent_1 → agent_2 pattern."""
    AgentState = create_agent_state_model({})
    GlobalState = create_agent_state_model({})
    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(name="global"),
    )

    manager = LifecycleManager()

    # Add first agent
    name1 = manager.add_agent("agent", DummyAgent("agent"), {}, state)
    assert name1 == "agent"

    # Add second agent with same name
    name2 = manager.add_agent("agent", DummyAgent("agent"), {}, state)
    assert name2 == "agent_1"

    # Add third agent with same name
    name3 = manager.add_agent("agent", DummyAgent("agent"), {}, state)
    assert name3 == "agent_2"

    # Verify all in state
    assert "agent" in state.agents
    assert "agent_1" in state.agents
    assert "agent_2" in state.agents
