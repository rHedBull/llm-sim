"""Contract tests for BaseValidator interface.
from llm_sim.models.state import GlobalState

These tests verify that the BaseValidator abstract interface remains stable
and that concrete implementations properly inherit from it.
"""

import pytest
from abc import ABC
from typing import List, Dict

from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class TestBaseValidatorContract:
    """Test BaseValidator interface contract."""

    def test_base_validator_is_abstract(self, mock_simulation_state):
        """BaseValidator should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseValidator()

    def test_validate_action_is_abstract_method(self, mock_simulation_state):
        """validate_action must be an abstract method."""
        assert hasattr(BaseValidator, 'validate_action')
        assert hasattr(BaseValidator.validate_action, '__isabstractmethod__')
        assert BaseValidator.validate_action.__isabstractmethod__ is True

    def test_validate_actions_has_default_implementation(self, mock_simulation_state):
        """validate_actions should have a default implementation."""
        assert hasattr(BaseValidator, 'validate_actions')
        assert not getattr(BaseValidator.validate_actions, '__isabstractmethod__', False)

    def test_get_stats_method_exists(self, mock_simulation_state):
        """get_stats should exist as a concrete method."""
        assert hasattr(BaseValidator, 'get_stats')
        assert not getattr(BaseValidator.get_stats, '__isabstractmethod__', False)

    def test_concrete_implementation_can_be_instantiated(self, mock_simulation_state):
        """A concrete class implementing validate_action can be instantiated."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = ConcreteValidator()
        assert isinstance(validator, BaseValidator)

    def test_concrete_implementation_without_validate_action_fails(self, mock_simulation_state):
        """A concrete class not implementing validate_action cannot be instantiated."""
        class IncompleteValidator(BaseValidator):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteValidator()

    def test_base_validator_inherits_from_abc(self, mock_simulation_state):
        """BaseValidator should inherit from ABC."""
        assert issubclass(BaseValidator, ABC)

    def test_validator_tracks_validation_count(self, mock_simulation_state):
        """Validator should have validation_count attribute."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = ConcreteValidator()
        assert hasattr(validator, 'validation_count')
        assert validator.validation_count == 0

    def test_validator_tracks_rejection_count(self, mock_simulation_state):
        """Validator should have rejection_count attribute."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = ConcreteValidator()
        assert hasattr(validator, 'rejection_count')
        assert validator.rejection_count == 0

    def test_validate_actions_calls_validate_action_for_each(self, mock_simulation_state):
        """validate_actions should call validate_action for each action."""
        class ConcreteValidator(BaseValidator):
            def __init__(self):
                super().__init__()
                self.call_count = 0

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                self.call_count += 1
                return True

        validator = ConcreteValidator()
        mock_state = mock_simulation_state
        actions = [
            Action(agent_name="agent1", action_name="test"),
            Action(agent_name="agent2", action_name="test"),
            Action(agent_name="agent3", action_name="test"),
        ]

        validator.validate_actions(actions, mock_state)
        assert validator.call_count == 3

    def test_validate_actions_filters_invalid_actions(self, mock_simulation_state):
        """validate_actions should filter out invalid actions."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                # Only allow actions from agent1
                return action.agent_name == "agent1"

        validator = ConcreteValidator()
        mock_state = mock_simulation_state
        actions = [
            Action(agent_name="agent1", action_name="test"),
            Action(agent_name="agent2", action_name="test"),
            Action(agent_name="agent1", action_name="test2"),
        ]

        valid_actions = validator.validate_actions(actions, mock_state)
        assert len(valid_actions) == 2
        assert all(a.agent_name == "agent1" for a in valid_actions)

    def test_get_stats_returns_dict(self, mock_simulation_state):
        """get_stats should return a dictionary with statistics."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = ConcreteValidator()
        stats = validator.get_stats()
        assert isinstance(stats, dict)

    def test_validate_actions_updates_validation_count(self, mock_simulation_state):
        """validate_actions should update validation_count."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = ConcreteValidator()
        mock_state = mock_simulation_state
        actions = [
            Action(agent_name="agent1", action_name="test"),
            Action(agent_name="agent2", action_name="test"),
        ]

        assert validator.validation_count == 0
        validator.validate_actions(actions, mock_state)
        assert validator.validation_count == 2

    def test_validate_actions_updates_rejection_count(self, mock_simulation_state):
        """validate_actions should update rejection_count for invalid actions."""
        class ConcreteValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return action.agent_name == "agent1"

        validator = ConcreteValidator()
        mock_state = mock_simulation_state
        actions = [
            Action(agent_name="agent1", action_name="test"),
            Action(agent_name="agent2", action_name="test"),
            Action(agent_name="agent3", action_name="test"),
        ]

        assert validator.rejection_count == 0
        validator.validate_actions(actions, mock_state)
        assert validator.rejection_count == 2  # agent2 and agent3 rejected
