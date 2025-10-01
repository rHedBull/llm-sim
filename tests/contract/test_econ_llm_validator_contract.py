"""
from llm_sim.models.state import GlobalState
Contract tests for EconLLMValidator concrete implementation.

These tests validate the economic domain-specific validation logic,
including domain boundary definitions and permissive validation.

Status: THESE TESTS MUST FAIL - EconLLMValidator not yet implemented
"""

import pytest
from unittest.mock import AsyncMock

# These imports will fail until implementation is complete
try:
    from llm_sim.implementations.validators.econ_llm_validator import EconLLMValidator
    from llm_sim.models.llm_models import ValidationResult
    from llm_sim.models.action import Action, LLMAction
    from llm_sim.models.state import SimulationState, GlobalState
except ImportError:
    pytest.skip("EconLLMValidator not yet implemented", allow_module_level=True)


@pytest.mark.asyncio
async def test_econ_validator_accepts_economic_action():
    """Verify economic action is validated"""
    # Given: Mock LLM returning is_valid=True
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = ValidationResult(
        is_valid=True,
        reasoning="This is economic policy within domain",
        confidence=0.95,
        action_evaluated="Lower interest rates"
    )

    validator = EconLLMValidator(
        llm_client=mock_client,
        domain="economic",
        permissive=True
    )

    actions = [
        LLMAction(
            agent_name="USA",
            action_name="Lower interest rates",
            validated=False
        )
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

    # When: Validating action
    validated_actions = await validator.validate_actions(actions, state)

    # Then: Action is marked validated
    assert validated_actions[0].validated is True
    assert validated_actions[0].validation_result.is_valid is True


@pytest.mark.asyncio
async def test_econ_validator_rejects_military_action():
    """Verify non-economic action is rejected"""
    # Given: Mock LLM returning is_valid=False
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = ValidationResult(
        is_valid=False,
        reasoning="Military actions are outside economic domain",
        confidence=0.90,
        action_evaluated="Deploy military forces"
    )

    validator = EconLLMValidator(
        llm_client=mock_client,
        domain="economic",
        permissive=True
    )

    actions = [
        LLMAction(
            agent_name="USA",
            action_name="Deploy military forces",
            validated=False
        )
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

    # When: Validating action
    validated_actions = await validator.validate_actions(actions, state)

    # Then: Action is not validated
    assert validated_actions[0].validated is False


@pytest.mark.asyncio
async def test_econ_validator_uses_permissive_approach():
    """Verify boundary case (trade sanctions) is accepted with permissive=True"""
    # Given: Mock LLM returning is_valid=True for boundary case
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = ValidationResult(
        is_valid=True,
        reasoning="Trade sanctions have significant economic impact, permissive validation accepts",
        confidence=0.75,
        action_evaluated="Impose trade sanctions"
    )

    validator = EconLLMValidator(
        llm_client=mock_client,
        domain="economic",
        permissive=True
    )

    actions = [
        LLMAction(
            agent_name="USA",
            action_name="Impose trade sanctions",
            validated=False
        )
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

    # When: Validating boundary case
    validated_actions = await validator.validate_actions(actions, state)

    # Then: Action is accepted with permissive validation
    assert validated_actions[0].validated is True


def test_econ_validator_domain_description():
    """Verify economic domain boundaries in description"""
    # Given: EconLLMValidator
    mock_client = AsyncMock()
    validator = EconLLMValidator(
        llm_client=mock_client,
        domain="economic",
        permissive=True
    )

    # When: Getting domain description
    description = validator._get_domain_description()

    # Then: Description includes economic boundaries
    assert "economic" in description.lower()
    assert any(keyword in description.lower() for keyword in [
        "interest", "fiscal", "trade", "tax", "monetary"
    ])
