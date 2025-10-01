"""Contract tests for LLMValidator pattern.
from llm_sim.models.state import GlobalState

These tests verify that the LLMValidator pattern class remains stable
and properly extends BaseValidator.
"""

import pytest
from abc import ABC
from typing import List

from llm_sim.infrastructure.base.validator import BaseValidator
from llm_sim.infrastructure.patterns.llm_validator import LLMValidator
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class TestLLMValidatorContract:
    """Test LLMValidator pattern contract."""

    def test_llm_validator_extends_base_validator(self):
        """LLMValidator should extend BaseValidator."""
        assert issubclass(LLMValidator, BaseValidator)

    def test_llm_validator_is_abstract(self):
        """LLMValidator should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LLMValidator(model="test_model")

    def test_construct_validation_prompt_is_abstract_method(self):
        """_construct_validation_prompt must be an abstract method."""
        assert hasattr(LLMValidator, '_construct_validation_prompt')
        assert hasattr(LLMValidator._construct_validation_prompt, '__isabstractmethod__')
        assert LLMValidator._construct_validation_prompt.__isabstractmethod__ is True

    def test_get_domain_description_is_abstract_method(self):
        """_get_domain_description must be an abstract method."""
        assert hasattr(LLMValidator, '_get_domain_description')
        assert hasattr(LLMValidator._get_domain_description, '__isabstractmethod__')
        assert LLMValidator._get_domain_description.__isabstractmethod__ is True

    def test_validate_actions_has_concrete_implementation(self):
        """validate_actions should have a concrete implementation."""
        assert hasattr(LLMValidator, 'validate_actions')
        # Should have implementation in LLMValidator (overrides base)
        assert 'validate_actions' in dir(LLMValidator)

    def test_concrete_implementation_can_be_instantiated(self):
        """A concrete class implementing all abstract methods can be instantiated."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.action import LLMAction

        class ConcreteLLMValidator(LLMValidator):
            def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
                return "validate these actions"

            def _get_domain_description(self) -> str:
                return "test domain"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        llm_config = LLMConfig(model="test_model", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        validator = ConcreteLLMValidator(llm_client=client, domain="test")
        assert isinstance(validator, LLMValidator)
        assert isinstance(validator, BaseValidator)

    def test_concrete_implementation_without_construct_prompt_fails(self):
        """A concrete class not implementing _construct_validation_prompt cannot be instantiated."""
        class IncompleteLLMValidator(LLMValidator):
            def _get_domain_description(self) -> str:
                return "test domain"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True
            # Missing: _construct_validation_prompt

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteLLMValidator(model="test_model")

    def test_concrete_implementation_without_domain_description_fails(self):
        """A concrete class not implementing _get_domain_description cannot be instantiated."""
        class IncompleteLLMValidator(LLMValidator):
            def _construct_validation_prompt(self, actions: List[Action], state: SimulationState) -> str:
                return "validate"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True
            # Missing: _get_domain_description

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteLLMValidator(model="test_model")

    def test_llm_validator_inherits_from_abc(self):
        """LLMValidator should inherit from ABC."""
        assert issubclass(LLMValidator, ABC)

    def test_concrete_implementation_preserves_model_attribute(self):
        """Concrete implementation should properly initialize model attribute."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.action import LLMAction

        class ConcreteLLMValidator(LLMValidator):
            def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
                return "validate"

            def _get_domain_description(self) -> str:
                return "test domain"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        llm_config = LLMConfig(model="gpt-4", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        validator = ConcreteLLMValidator(llm_client=client, domain="test")
        assert hasattr(validator, 'llm_client')
        assert validator.llm_client.config.model == "gpt-4"

    def test_llm_validator_has_client_attribute(self):
        """LLMValidator should have a client attribute for LLM communication."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.action import LLMAction

        class ConcreteLLMValidator(LLMValidator):
            def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
                return "validate"

            def _get_domain_description(self) -> str:
                return "test domain"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        llm_config = LLMConfig(model="test_model", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        validator = ConcreteLLMValidator(llm_client=client, domain="test")
        assert hasattr(validator, 'llm_client')

    def test_llm_validator_inherits_stats_tracking(self):
        """LLMValidator should inherit validation_count and rejection_count from BaseValidator."""
        from llm_sim.utils.llm_client import LLMClient
        from llm_sim.models.config import LLMConfig
        from llm_sim.models.action import LLMAction

        class ConcreteLLMValidator(LLMValidator):
            def _construct_validation_prompt(self, action: LLMAction, state: SimulationState) -> str:
                return "validate"

            def _get_domain_description(self) -> str:
                return "test domain"

            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        llm_config = LLMConfig(model="test_model", temperature=0.7, max_retries=3)
        client = LLMClient(llm_config)
        validator = ConcreteLLMValidator(llm_client=client, domain="test")
        assert hasattr(validator, 'validation_count')
        assert hasattr(validator, 'rejection_count')
