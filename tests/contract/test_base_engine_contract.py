"""Contract tests for BaseEngine interface.
from llm_sim.models.state import GlobalState

These tests verify that the BaseEngine abstract interface remains stable
and that concrete implementations properly inherit from it.
"""

import pytest
from abc import ABC
from typing import List

from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from llm_sim.models.config import SimulationConfig


class TestBaseEngineContract:
    """Test BaseEngine interface contract."""

    def test_base_engine_is_abstract(self, mock_config):
        """BaseEngine should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseEngine(config=mock_config)

    def test_initialize_state_is_abstract_method(self, mock_config):
        """initialize_state must be an abstract method."""
        assert hasattr(BaseEngine, 'initialize_state')
        assert hasattr(BaseEngine.initialize_state, '__isabstractmethod__')
        assert BaseEngine.initialize_state.__isabstractmethod__ is True

    def test_apply_actions_is_abstract_method(self, mock_config):
        """apply_actions must be an abstract method."""
        assert hasattr(BaseEngine, 'apply_actions')
        assert hasattr(BaseEngine.apply_actions, '__isabstractmethod__')
        assert BaseEngine.apply_actions.__isabstractmethod__ is True

    def test_apply_engine_rules_is_abstract_method(self, mock_config):
        """apply_engine_rules must be an abstract method."""
        assert hasattr(BaseEngine, 'apply_engine_rules')
        assert hasattr(BaseEngine.apply_engine_rules, '__isabstractmethod__')
        assert BaseEngine.apply_engine_rules.__isabstractmethod__ is True

    def test_check_termination_is_abstract_method(self, mock_config):
        """check_termination must be an abstract method."""
        assert hasattr(BaseEngine, 'check_termination')
        assert hasattr(BaseEngine.check_termination, '__isabstractmethod__')
        assert BaseEngine.check_termination.__isabstractmethod__ is True

    def test_run_turn_method_exists(self, mock_config):
        """run_turn should exist as a concrete method."""
        assert hasattr(BaseEngine, 'run_turn')
        # run_turn should NOT be abstract (it has default implementation)
        assert not getattr(BaseEngine.run_turn, '__isabstractmethod__', False)

    def test_concrete_implementation_can_be_instantiated(self, mock_config):
        """A concrete class implementing all abstract methods can be instantiated."""
        class ConcreteEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state={})

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return state.turn >= 10

        # Using mock_config fixture
        engine = ConcreteEngine(config=mock_config)
        assert isinstance(engine, BaseEngine)

    def test_concrete_implementation_without_all_methods_fails(self, mock_config):
        """A concrete class not implementing all abstract methods cannot be instantiated."""
        class IncompleteEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state={})
            # Missing: apply_actions, apply_engine_rules, check_termination

        # Using mock_config fixture
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteEngine(config=mock_config)

    def test_base_engine_inherits_from_abc(self, mock_config):
        """BaseEngine should inherit from ABC."""
        assert issubclass(BaseEngine, ABC)

    def test_concrete_implementation_preserves_config(self, mock_config):
        """Concrete implementation should properly initialize config attribute."""
        class ConcreteEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state={})

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

        # Using mock_config fixture
        engine = ConcreteEngine(config=mock_config)
        assert hasattr(engine, 'config')
        assert engine.config == mock_config

    def test_engine_initializes_state_attribute(self, mock_config):
        """Engine should have _state attribute after initialization."""
        class ConcreteEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state={})

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

        # Using mock_config fixture
        engine = ConcreteEngine(config=mock_config)
        assert hasattr(engine, '_state')

    def test_engine_has_turn_counter(self, mock_config):
        """Engine should have _turn_counter attribute."""
        class ConcreteEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(turn=0, agents={}, global_state={})

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

        # Using mock_config fixture
        engine = ConcreteEngine(config=mock_config)
        assert hasattr(engine, '_turn_counter')
