"""Contract tests for LLMEngine pattern.
from llm_sim.models.state import GlobalState

These tests verify that the LLMEngine pattern class remains stable
and properly extends BaseEngine.
"""

import pytest
from abc import ABC
from typing import List

from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.infrastructure.patterns.llm_engine import LLMEngine
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from llm_sim.models.config import SimulationConfig


class TestLLMEngineContract:
    """Test LLMEngine pattern contract."""

    def test_llm_engine_extends_base_engine(self, mock_config):
        """LLMEngine should extend BaseEngine."""
        assert issubclass(LLMEngine, BaseEngine)

    def test_llm_engine_is_abstract(self, mock_config):
        """LLMEngine should be abstract and cannot be instantiated."""
        # Using fixture
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LLMEngine(config=mock_config)

    def test_construct_state_update_prompt_is_abstract_method(self, mock_config):
        """_construct_state_update_prompt must be an abstract method."""
        assert hasattr(LLMEngine, '_construct_state_update_prompt')
        assert hasattr(LLMEngine._construct_state_update_prompt, '__isabstractmethod__')
        assert LLMEngine._construct_state_update_prompt.__isabstractmethod__ is True

    def test_apply_state_update_is_abstract_method(self, mock_config):
        """_apply_state_update must be an abstract method."""
        assert hasattr(LLMEngine, '_apply_state_update')
        assert hasattr(LLMEngine._apply_state_update, '__isabstractmethod__')
        assert LLMEngine._apply_state_update.__isabstractmethod__ is True

    def test_run_turn_has_concrete_implementation(self, mock_config):
        """run_turn should have a concrete implementation."""
        assert hasattr(LLMEngine, 'run_turn')
        # run_turn is implemented in BaseEngine, should not be abstract
        assert not getattr(LLMEngine.run_turn, '__isabstractmethod__', False)

    def test_concrete_implementation_can_be_instantiated(self, mock_config):
        """A concrete class implementing all abstract methods can be instantiated."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.llm_models import StateUpdateDecision

        class ConcreteLLMEngine(LLMEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state=GlobalState(interest_rate=0.05))

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self.current_state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

            def _construct_state_update_prompt(self, action: Action, state) -> str:
                return "test prompt"

            def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
                return state

        # Using fixture
        llm_config = LLMConfig(model="test_model", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        engine = ConcreteLLMEngine(config=mock_config, llm_client=client)
        assert isinstance(engine, LLMEngine)
        assert isinstance(engine, BaseEngine)

    def test_concrete_implementation_without_construct_prompt_fails(self, mock_config):
        """A concrete class not implementing _construct_state_update_prompt cannot be instantiated."""
        class IncompleteLLMEngine(LLMEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state=GlobalState(interest_rate=0.05))

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

            def _apply_state_update(self, update_text: str) -> SimulationState:
                return self._state
            # Missing: _construct_state_update_prompt

        # Using fixture
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteLLMEngine(config=mock_config)

    def test_llm_engine_inherits_from_abc(self, mock_config):
        """LLMEngine should inherit from ABC."""
        assert issubclass(LLMEngine, ABC)

    def test_concrete_implementation_preserves_model_attribute(self, mock_config):
        """Concrete implementation should have access to model from config."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.llm_models import StateUpdateDecision

        class ConcreteLLMEngine(LLMEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state=GlobalState(interest_rate=0.05))

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self.current_state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

            def _construct_state_update_prompt(self, action: Action, state) -> str:
                return "test prompt"

            def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
                return state

        # Using fixture
        llm_config = LLMConfig(model="test_model", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        engine = ConcreteLLMEngine(config=mock_config, llm_client=client)
        assert hasattr(engine, 'llm_client')
