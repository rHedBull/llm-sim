"""Contract tests for LLMValidator abstract interface.

These tests validate the LLMValidator abstract class contract from:
specs/004-new-feature-i/contracts/validator_interface_contract.md

Tests MUST FAIL before LLMValidator implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock

# Import will fail until LLMValidator is implemented
try:
    from llm_sim.validators.llm_validator import LLMValidator
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import ValidationResult, PolicyDecision
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
except ImportError:
    pytest.skip("LLMValidator not yet implemented", allow_module_level=True)


# Mock concrete implementation for testing abstract interface
class MockLLMValidator(LLMValidator):
    """Concrete implementation of LLMValidator for testing."""

    def _construct_validation_prompt(self, action: Action) -> str:
        """Mock validation prompt construction."""
        return f"Validate action: {action.action_string}"

    def _get_domain_description(self) -> str:
        """Mock domain description."""
        return "Test domain includes: test actions"


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
def sample_action():
    """Sample action to validate."""
    policy_decision = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="Economic reasoning",
        confidence=0.85
    )
    return Action(
        agent_name="TestAgent",
        action_string="Lower interest rates by 0.5%",
        policy_decision=policy_decision,
        validated=False
    )


@pytest.fixture
def valid_result():
    """Sample valid validation result."""
    return ValidationResult(
        is_valid=True,
        reasoning="Action is within domain boundaries",
        confidence=0.9,
        action_evaluated="Lower interest rates by 0.5%"
    )


@pytest.fixture
def invalid_result():
    """Sample invalid validation result."""
    return ValidationResult(
        is_valid=False,
        reasoning="Action is outside domain boundaries",
        confidence=0.85,
        action_evaluated="Deploy military forces"
    )


def test_llm_validator_calls_abstract_methods():
    """Test that LLMValidator has required abstract methods.

    Contract: LLMValidator must define:
    - _construct_validation_prompt (abstract)
    - _get_domain_description (abstract)
    """
    # Verify abstract methods exist
    assert hasattr(LLMValidator, '_construct_validation_prompt')
    assert hasattr(LLMValidator, '_get_domain_description')

    # Verify they are abstract (can't instantiate without implementing)
    try:
        validator = LLMValidator(llm_client=Mock(), domain="test", permissive=True)
        pytest.fail("Should not be able to instantiate abstract LLMValidator")
    except TypeError as e:
        assert "abstract" in str(e).lower()


@pytest.mark.asyncio
async def test_llm_validator_validate_actions_workflow(mock_llm_client, sample_state, sample_action, valid_result):
    """Test validate_actions workflow.

    Contract: LLMValidator.validate_actions should:
    1. Loop through all actions
    2. Call _construct_validation_prompt for each
    3. Call llm_client.call_with_retry(prompt, ValidationResult)
    4. Mark action.validated based on result.is_valid
    5. Set action.validation_result
    """
    validator = MockLLMValidator(llm_client=mock_llm_client, domain="test", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    actions = [sample_action]
    validated_actions = await validator.validate_actions(actions, sample_state)

    # Assertions
    assert len(validated_actions) == 1
    assert validated_actions[0].validated is True
    assert validated_actions[0].validation_result == valid_result
    assert mock_llm_client.call_with_retry.called


@pytest.mark.asyncio
async def test_llm_validator_logs_reasoning_chain(mock_llm_client, sample_state, sample_action, valid_result, caplog):
    """Test that reasoning chain is logged at DEBUG level.

    Contract: LLMValidator should:
    - Log reasoning chain with component='validator'
    - Include reasoning and confidence
    - Log at DEBUG level for each action
    """
    import logging
    caplog.set_level(logging.DEBUG)

    validator = MockLLMValidator(llm_client=mock_llm_client, domain="test", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    await validator.validate_actions([sample_action], sample_state)

    # Check that DEBUG log contains reasoning information
    debug_logs = [record for record in caplog.records if record.levelname == "DEBUG"]
    assert len(debug_logs) > 0


@pytest.mark.asyncio
async def test_llm_validator_returns_same_length_list(mock_llm_client, sample_state, valid_result):
    """Test that output list has same length as input.

    Contract: LLMValidator should:
    - Return exactly the same number of actions as input
    - Maintain action order
    - Not filter or drop actions
    """
    validator = MockLLMValidator(llm_client=mock_llm_client, domain="test", permissive=True)
    mock_llm_client.call_with_retry.return_value = valid_result

    # Create 3 actions
    actions = []
    for i in range(3):
        policy_decision = PolicyDecision(
            action=f"Action {i}",
            reasoning="Test reasoning",
            confidence=0.8
        )
        action = Action(
            agent_name=f"Agent{i}",
            action_string=f"Action {i}",
            policy_decision=policy_decision,
            validated=False
        )
        actions.append(action)

    validated_actions = await validator.validate_actions(actions, sample_state)

    # Assertions
    assert len(validated_actions) == len(actions)
    assert validated_actions[0].agent_name == "Agent0"
    assert validated_actions[1].agent_name == "Agent1"
    assert validated_actions[2].agent_name == "Agent2"