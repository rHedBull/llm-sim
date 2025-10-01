"""Contract tests for BaseAgent interface.

These tests verify that the BaseAgent abstract interface remains stable
and that concrete implementations properly inherit from it.
"""

import pytest
from abc import ABC

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class TestBaseAgentContract:
    """Test BaseAgent interface contract."""

    def test_base_agent_is_abstract(self):
        """BaseAgent should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgent(name="test")

    def test_decide_action_is_abstract_method(self):
        """decide_action must be an abstract method."""
        # Verify it's marked as abstract
        assert hasattr(BaseAgent, 'decide_action')
        assert hasattr(BaseAgent.decide_action, '__isabstractmethod__')
        assert BaseAgent.decide_action.__isabstractmethod__ is True

    def test_receive_state_has_default_implementation(self):
        """receive_state should have a default implementation."""
        # Verify method exists and is not abstract
        assert hasattr(BaseAgent, 'receive_state')
        assert not getattr(BaseAgent.receive_state, '__isabstractmethod__', False)

    def test_get_current_state_returns_none_initially(self):
        """get_current_state should return None before any state is set."""
        # Create a concrete implementation for testing
        class ConcreteAgent(BaseAgent):
            def decide_action(self, state: SimulationState) -> Action:
                return Action(agent_name=self.name, action_name="test")

        agent = ConcreteAgent(name="test_agent")
        assert agent.get_current_state() is None

    def test_concrete_implementation_can_be_instantiated(self):
        """A concrete class implementing decide_action can be instantiated."""
        class ConcreteAgent(BaseAgent):
            def decide_action(self, state: SimulationState) -> Action:
                return Action(agent_name=self.name, action_name="test")

        agent = ConcreteAgent(name="test_agent")
        assert isinstance(agent, BaseAgent)
        assert agent.name == "test_agent"

    def test_concrete_implementation_without_decide_action_fails(self):
        """A concrete class not implementing decide_action cannot be instantiated."""
        class IncompleteAgent(BaseAgent):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteAgent(name="test")

    def test_receive_state_updates_internal_state(self, GlobalState):
        """receive_state should update the agent's internal state."""
        class ConcreteAgent(BaseAgent):
            def decide_action(self, state: SimulationState) -> Action:
                return Action(agent_name=self.name, action_name="test")

        agent = ConcreteAgent(name="test_agent")
        mock_state = SimulationState(
            turn=1,
            agents={},
            global_state=GlobalState(interest_rate=5.0)
        )

        # Initially None
        assert agent.get_current_state() is None

        # After receive_state, should be set
        agent.receive_state(mock_state)
        assert agent.get_current_state() is not None
        assert agent.get_current_state().turn == 1

    def test_base_agent_inherits_from_abc(self):
        """BaseAgent should inherit from ABC."""
        assert issubclass(BaseAgent, ABC)

    def test_concrete_implementation_preserves_name(self):
        """Concrete implementation should properly initialize name attribute."""
        class ConcreteAgent(BaseAgent):
            def decide_action(self, state: SimulationState) -> Action:
                return Action(agent_name=self.name, action_name="test")

        agent = ConcreteAgent(name="my_agent")
        assert hasattr(agent, 'name')
        assert agent.name == "my_agent"
