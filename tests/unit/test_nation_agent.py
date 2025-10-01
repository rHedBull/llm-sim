"""Tests for the Nation Agent."""

import pytest

from llm_sim.models.state import SimulationState
from llm_sim.implementations.agents.nation import NationAgent


class TestNationAgent:
    """Tests for NationAgent implementation."""

    def test_create_agent(self, AgentState, GlobalState) -> None:
        """Test creating a nation agent."""
        agent = NationAgent(name="Nation_A")
        assert agent.name == "Nation_A"
        assert agent.strategy == "grow"  # Default

        agent_maintain = NationAgent(name="Nation_B", strategy="maintain")
        assert agent_maintain.strategy == "maintain"

        agent_decline = NationAgent(name="Nation_C", strategy="decline")
        assert agent_decline.strategy == "decline"

    def test_decide_action_grow(self, AgentState, GlobalState) -> None:
        """Test growth strategy action."""
        agent = NationAgent(name="Nation_A", strategy="grow")

        state = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        action = agent.decide_action(state)

        assert action.agent_name == "Nation_A"
        assert action.action_name == "grow"
        assert action.parameters["strength"] == 1000.0
        assert not action.validated

    def test_decide_action_maintain(self, AgentState, GlobalState) -> None:
        """Test maintain strategy action."""
        agent = NationAgent(name="Nation_B", strategy="maintain")

        state = SimulationState(
            turn=1,
            agents={"Nation_B": AgentState(name="Nation_B", economic_strength=2000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=2000.0),
        )

        action = agent.decide_action(state)

        assert action.agent_name == "Nation_B"
        assert action.action_name == "maintain"
        assert action.parameters["strength"] == 2000.0

    def test_decide_action_decline(self, AgentState, GlobalState) -> None:
        """Test decline strategy action."""
        agent = NationAgent(name="Nation_C", strategy="decline")

        state = SimulationState(
            turn=1,
            agents={"Nation_C": AgentState(name="Nation_C", economic_strength=500.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=500.0),
        )

        action = agent.decide_action(state)

        assert action.agent_name == "Nation_C"
        assert action.action_name == "decline"
        assert action.parameters["strength"] == 500.0

    def test_receive_state(self, AgentState, GlobalState) -> None:
        """Test state reception."""
        agent = NationAgent(name="Nation_A")

        assert agent.get_current_state() is None

        state = SimulationState(
            turn=5,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=1500.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1500.0),
        )

        agent.receive_state(state)

        received_state = agent.get_current_state()
        assert received_state is not None
        assert received_state.turn == 5
        assert received_state.agents["Nation_A"].economic_strength == 1500.0

    def test_invalid_strategy(self, AgentState, GlobalState) -> None:
        """Test that invalid strategy raises error."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            NationAgent(name="Nation_X", strategy="invalid")

    def test_agent_not_in_state(self, AgentState, GlobalState) -> None:
        """Test error when agent not in state."""
        agent = NationAgent(name="Nation_A")

        state = SimulationState(
            turn=1,
            agents={"Nation_B": AgentState(name="Nation_B", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        with pytest.raises(KeyError, match="Nation_A"):
            agent.decide_action(state)
