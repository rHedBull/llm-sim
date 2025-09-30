"""Contract tests for EconLLMValidator concrete implementation.

These tests validate the EconLLMValidator contract from:
specs/004-new-feature-i/contracts/validator_interface_contract.md

Tests MUST FAIL before EconLLMValidator implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock

# Import will fail until EconLLMValidator is implemented
try:
    from llm_sim.validators.econ_llm_validator import EconLLMValidator
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import ValidationResult, PolicyDecision
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
except ImportError:
    pytest.skip("EconLLMValidator not yet implemented", allow_module_level=True)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.call_with_retry = AsyncMock()
    return client


@pytest.fixture
def sample_state():
    """Sample simulation state."""
    global_state = GlobalState(
        gdp_growth=2.5,
        inflation=3.0,
        unemployment=5.0,
        interest_rate=2.5
    )
    return SimulationState(
        turn=1,
        agents={},
        global_state=global_state,
        reasoning_chains=[]
    )


@pytest.fixture
def economic_action():
    """Sample economic action."""
    policy_decision = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="Economic policy reasoning",
        confidence=0.85
    )
    return Action(
        agent_name="TestAgent",
        action_string="Lower interest rates by 0.5%",
        policy_decision=policy_decision,
        validated=False
    )


@pytest.fixture
def military_action():
    """Sample military action (non-economic)."""
    policy_decision = PolicyDecision(
        action="Deploy military forces to border",
        reasoning="Military reasoning",
        confidence=0.8
    )
    return Action(
        agent_name="TestAgent",
        action_string="Deploy military forces to border",
        policy_decision=policy_decision,
        validated=False
    )


@pytest.fixture
def boundary_action():
    """Sample boundary case action (trade sanctions - economic + military)."""
    policy_decision = PolicyDecision(
        action="Impose trade sanctions on neighboring country",
        reasoning="Economic pressure reasoning",
        confidence=0.75
    )
    return Action(
        agent_name="TestAgent",
        action_string="Impose trade sanctions on neighboring country",
        policy_decision=policy_decision,
        validated=False
    )


@pytest.mark.asyncio
async def test_econ_validator_accepts_economic_action(mock_llm_client, sample_state, economic_action):
    """Test that economic actions are accepted.

    Contract: EconLLMValidator should:
    - Use LLM to determine if action is economic
    - Accept actions within economic domain
    - Mark action as validated=True
    """
    valid_result = ValidationResult(
        is_valid=True,
        reasoning="Action targets interest rates, which is core economic policy",
        confidence=0.9,
        action_evaluated="Lower interest rates by 0.5%"
    )

    validator = EconLLMValidator(llm_client=mock_llm_client, domain="economic", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    validated_actions = await validator.validate_actions([economic_action], sample_state)

    # Assertions
    assert validated_actions[0].validated is True
    assert validated_actions[0].validation_result.is_valid is True


@pytest.mark.asyncio
async def test_econ_validator_rejects_military_action(mock_llm_client, sample_state, military_action):
    """Test that non-economic actions are rejected.

    Contract: EconLLMValidator should:
    - Use LLM to determine if action is economic
    - Reject actions outside economic domain
    - Mark action as validated=False
    """
    invalid_result = ValidationResult(
        is_valid=False,
        reasoning="Military deployment is not economic policy, falls under defense domain",
        confidence=0.95,
        action_evaluated="Deploy military forces to border"
    )

    validator = EconLLMValidator(llm_client=mock_llm_client, domain="economic", permissive=True)
    mock_llm_client.call_with_retry.return_value = invalid_result

    validated_actions = await validator.validate_actions([military_action], sample_state)

    # Assertions
    assert validated_actions[0].validated is False
    assert validated_actions[0].validation_result.is_valid is False


@pytest.mark.asyncio
async def test_econ_validator_uses_permissive_approach(mock_llm_client, sample_state, boundary_action):
    """Test permissive validation for boundary cases.

    Contract: EconLLMValidator should:
    - Use permissive=True by default (per spec FR-005a)
    - Accept actions with ANY significant economic impact
    - Accept trade sanctions (economic + diplomatic boundary case)
    """
    # Trade sanctions have economic impact, should be accepted in permissive mode
    valid_result = ValidationResult(
        is_valid=True,
        reasoning="Trade sanctions have significant economic impact, affecting trade balance and GDP",
        confidence=0.8,
        action_evaluated="Impose trade sanctions on neighboring country"
    )

    validator = EconLLMValidator(llm_client=mock_llm_client, domain="economic", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    validated_actions = await validator.validate_actions([boundary_action], sample_state)

    # Assertions
    assert validated_actions[0].validated is True
    assert validator.permissive is True


@pytest.mark.asyncio
async def test_econ_validator_domain_description(mock_llm_client, sample_state, economic_action):
    """Test that domain description includes economic boundaries.

    Contract: EconLLMValidator._get_domain_description should:
    - Define economic domain clearly
    - Include: interest rates, fiscal policy, trade, taxation, monetary policy
    - Exclude: military, social policy, pure diplomacy
    """
    valid_result = ValidationResult(
        is_valid=True,
        reasoning="Economic action",
        confidence=0.9,
        action_evaluated="Lower interest rates by 0.5%"
    )

    validator = EconLLMValidator(llm_client=mock_llm_client, domain="economic", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    # Get domain description
    domain_desc = validator._get_domain_description()

    # Verify economic keywords are present
    assert "economic" in domain_desc.lower()
    assert any(keyword in domain_desc.lower() for keyword in ["interest", "fiscal", "trade", "tax", "monetary"])

    # Verify non-economic domains are mentioned as exclusions
    assert any(keyword in domain_desc.lower() for keyword in ["military", "social"])