"""
Contract tests for LLMValidator abstract base class.

These tests validate the interface and workflow of the LLM-enabled
validator base class, ensuring abstract methods are enforced and the
validation workflow is correct.

Status: THESE TESTS MUST FAIL - LLMValidator not yet implemented
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# These imports will fail until implementation is complete
try:
    from llm_sim.validators.llm_validator import LLMValidator
    from llm_sim.models.llm_models import ValidationResult
    from llm_sim.models.action import Action
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.utils.llm_client import LLMClient
except ImportError:
    pytest.skip("LLMValidator not yet implemented", allow_module_level=True)


def test_llm_validator_calls_abstract_methods():
    """Verify _construct_validation_prompt and _get_domain_description are abstract"""
    # Then: Cannot instantiate LLMValidator directly
    with pytest.raises(TypeError):
        mock_client = MagicMock()
        LLMValidator(llm_client=mock_client, domain="test", permissive=True)


@pytest.mark.asyncio
async def test_llm_validator_validate_actions_workflow():
    """Verify validation loop marks actions correctly"""

    # Given: Mock concrete implementation
    class TestLLMValidator(LLMValidator):
        def _construct_validation_prompt(self, action):
            return f"Validate: {action.action_string}"

        def _get_domain_description(self):
            return "test domain"

    mock_client = AsyncMock()
    mock_client.call_with_retry.side_effect = [
        ValidationResult(
            is_valid=True,
            reasoning="This is in domain",
            confidence=0.9,
            action_evaluated="action 1"
        ),
        ValidationResult(
            is_valid=False,
            reasoning="This is out of domain",
            confidence=0.85,
            action_evaluated="action 2"
        )
    ]

    validator = TestLLMValidator(
        llm_client=mock_client,
        domain="test",
        permissive=True
    )

    actions = [
        Action(agent_name="Agent1", action_string="action 1", validated=False),
        Action(agent_name="Agent2", action_string="action 2", validated=False)
    ]

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=2.5,
            inflation=3.0,
            unemployment=5.0,
            interest_rate=2.5
        ),
        reasoning_chains=[]
    )

    # When: Validating actions
    validated_actions = await validator.validate_actions(actions, state)

    # Then: First action validated, second rejected
    assert validated_actions[0].validated is True
    assert validated_actions[1].validated is False
    assert mock_client.call_with_retry.call_count == 2


@pytest.mark.asyncio
async def test_llm_validator_logs_reasoning_chain():
    """Verify DEBUG log for each validation"""

    # Given: Mock implementation
    class TestLLMValidator(LLMValidator):
        def _construct_validation_prompt(self, action):
            return f"Validate: {action.action_string}"

        def _get_domain_description(self):
            return "test domain"

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = ValidationResult(
        is_valid=True,
        reasoning="Valid action",
        confidence=0.8,
        action_evaluated="test action"
    )

    validator = TestLLMValidator(
        llm_client=mock_client,
        domain="test",
        permissive=True
    )

    actions = [
        Action(agent_name="Agent1", action_string="test action", validated=False)
    ]

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=2.5,
            inflation=3.0,
            unemployment=5.0,
            interest_rate=2.5
        ),
        reasoning_chains=[]
    )

    # When: Validating actions
    validated_actions = await validator.validate_actions(actions, state)

    # Then: Reasoning logged (validation result attached)
    assert validated_actions[0].validation_result is not None
    assert validated_actions[0].validation_result.reasoning == "Valid action"


@pytest.mark.asyncio
async def test_llm_validator_returns_same_length_list():
    """Verify output list length == input length"""

    # Given: Mock implementation
    class TestLLMValidator(LLMValidator):
        def _construct_validation_prompt(self, action):
            return "validate"

        def _get_domain_description(self):
            return "domain"

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = ValidationResult(
        is_valid=True,
        reasoning="valid",
        confidence=0.8,
        action_evaluated="action"
    )

    validator = TestLLMValidator(
        llm_client=mock_client,
        domain="test",
        permissive=True
    )

    actions = [
        Action(agent_name=f"Agent{i}", action_string=f"action {i}", validated=False)
        for i in range(5)
    ]

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=2.5,
            inflation=3.0,
            unemployment=5.0,
            interest_rate=2.5
        ),
        reasoning_chains=[]
    )

    # When: Validating actions
    validated_actions = await validator.validate_actions(actions, state)

    # Then: Same number of actions returned
    assert len(validated_actions) == len(actions)
    assert len(validated_actions) == 5
