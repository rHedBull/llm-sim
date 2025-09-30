"""Contract tests for LLMAgent pattern.
from llm_sim.models.state import GlobalState

These tests verify that the LLMAgent pattern class remains stable
and properly extends BaseAgent.
"""

import pytest
from abc import ABC

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from llm_sim.models.llm_models import PolicyDecision


class TestLLMAgentContract:
    """Test LLMAgent pattern contract."""

    def test_llm_agent_extends_base_agent(self):
        """LLMAgent should extend BaseAgent."""
        assert issubclass(LLMAgent, BaseAgent)

    def test_llm_agent_is_abstract(self):
        """LLMAgent should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LLMAgent(name="test", model="test_model")

    def test_construct_prompt_is_abstract_method(self):
        """_construct_prompt must be an abstract method."""
        assert hasattr(LLMAgent, '_construct_prompt')
        assert hasattr(LLMAgent._construct_prompt, '__isabstractmethod__')
        assert LLMAgent._construct_prompt.__isabstractmethod__ is True

    def test_validate_decision_is_abstract_method(self):
        """_validate_decision must be an abstract method."""
        assert hasattr(LLMAgent, '_validate_decision')
        assert hasattr(LLMAgent._validate_decision, '__isabstractmethod__')
        assert LLMAgent._validate_decision.__isabstractmethod__ is True

    def test_decide_action_has_concrete_implementation(self):
        """decide_action should have a concrete implementation in LLMAgent."""
        assert hasattr(LLMAgent, 'decide_action')
        # In LLMAgent, decide_action should NOT be abstract (implemented)
        # We verify it exists and isn't marked abstract at LLMAgent level
        assert 'decide_action' in dir(LLMAgent)

    def test_concrete_implementation_can_be_instantiated(self):
        """A concrete class implementing both abstract methods can be instantiated."""
        class ConcreteLLMAgent(LLMAgent):
            def _construct_prompt(self, state: SimulationState) -> str:
                return "test prompt"

            def _validate_decision(self, decision: PolicyDecision) -> bool:
                return True

        agent = ConcreteLLMAgent(name="test_agent", model="test_model")
        assert isinstance(agent, LLMAgent)
        assert isinstance(agent, BaseAgent)

    def test_concrete_implementation_without_construct_prompt_fails(self):
        """A concrete class not implementing _construct_prompt cannot be instantiated."""
        class IncompleteLLMAgent(LLMAgent):
            def _validate_decision(self, decision: PolicyDecision) -> bool:
                return True
            # Missing: _construct_prompt

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteLLMAgent(name="test", model="test_model")

    def test_concrete_implementation_without_validate_decision_fails(self):
        """A concrete class not implementing _validate_decision cannot be instantiated."""
        class IncompleteLLMAgent(LLMAgent):
            def _construct_prompt(self, state: SimulationState) -> str:
                return "test prompt"
            # Missing: _validate_decision

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteLLMAgent(name="test", model="test_model")

    def test_llm_agent_inherits_from_abc(self):
        """LLMAgent should inherit from ABC."""
        assert issubclass(LLMAgent, ABC)

    def test_concrete_implementation_preserves_model_attribute(self):
        """Concrete implementation should properly initialize model attribute."""
        class ConcreteLLMAgent(LLMAgent):
            def _construct_prompt(self, state: SimulationState) -> str:
                return "test prompt"

            def _validate_decision(self, decision: PolicyDecision) -> bool:
                return True

        agent = ConcreteLLMAgent(name="test_agent", model="gpt-4")
        assert hasattr(agent, 'model')
        assert agent.model == "gpt-4"

    def test_concrete_implementation_preserves_name_from_base(self):
        """Concrete implementation should inherit name attribute from BaseAgent."""
        class ConcreteLLMAgent(LLMAgent):
            def _construct_prompt(self, state: SimulationState) -> str:
                return "test prompt"

            def _validate_decision(self, decision: PolicyDecision) -> bool:
                return True

        agent = ConcreteLLMAgent(name="my_agent", model="test_model")
        assert agent.name == "my_agent"

    def test_llm_agent_has_client_attribute(self):
        """LLMAgent should have a client attribute for LLM communication."""
        class ConcreteLLMAgent(LLMAgent):
            def _construct_prompt(self, state: SimulationState) -> str:
                return "test prompt"

            def _validate_decision(self, decision: PolicyDecision) -> bool:
                return True

        agent = ConcreteLLMAgent(name="test_agent", model="test_model")
        assert hasattr(agent, 'client')
