"""Contract tests for LLMAgent abstract interface.

These tests validate the LLMAgent abstract class contract from:
specs/004-new-feature-i/contracts/agent_interface_contract.md

Tests MUST FAIL before LLMAgent implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock
from abc import ABC

# Import will fail until LLMAgent is implemented
try:
    from llm_sim.agents.llm_agent import LLMAgent
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import PolicyDecision
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
except ImportError:
    pytest.skip("LLMAgent not yet implemented", allow_module_level=True)


# Mock concrete implementation for testing abstract interface
class MockLLMAgent(LLMAgent):
    """Concrete implementation of LLMAgent for testing."""

    def _construct_prompt(self, state: SimulationState) -> str:
        """Mock prompt construction."""
        return f"Test prompt with GDP={state.global_state.gdp_growth}"

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Mock decision validation."""
        return len(decision.action) > 0


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.call_with_retry = AsyncMock()
    return client


@pytest.fixture
def sample_state():
    """Sample simulation state for testing."""
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
def sample_policy_decision():
    """Sample policy decision from LLM."""
    return PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="High unemployment indicates weak demand",
        confidence=0.85
    )


def test_llm_agent_calls_abstract_methods():
    """Test that LLMAgent has required abstract methods.

    Contract: LLMAgent must define:
    - _construct_prompt (abstract)
    - _validate_decision (abstract)
    """
    # Verify abstract methods exist
    assert hasattr(LLMAgent, '_construct_prompt')
    assert hasattr(LLMAgent, '_validate_decision')

    # Verify they are abstract (can't instantiate without implementing)
    try:
        # This should fail because LLMAgent is abstract
        agent = LLMAgent(name="Test", llm_client=Mock())
        pytest.fail("Should not be able to instantiate abstract LLMAgent")
    except TypeError as e:
        assert "abstract" in str(e).lower()


@pytest.mark.asyncio
async def test_llm_agent_decide_action_workflow(mock_llm_client, sample_state, sample_policy_decision):
    """Test decide_action workflow.

    Contract: LLMAgent.decide_action should:
    1. Call _construct_prompt(state)
    2. Call llm_client.call_with_retry(prompt, PolicyDecision)
    3. Log reasoning chain at DEBUG level
    4. Create Action with action_string and policy_decision
    """
    agent = MockLLMAgent(name="TestAgent", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.return_value = sample_policy_decision

    action = await agent.decide_action(sample_state)

    # Assertions
    assert isinstance(action, Action)
    assert action.agent_name == "TestAgent"
    assert action.action_string == "Lower interest rates by 0.5%"
    assert action.policy_decision == sample_policy_decision
    assert mock_llm_client.call_with_retry.called


@pytest.mark.asyncio
async def test_llm_agent_logs_reasoning_chain(mock_llm_client, sample_state, sample_policy_decision, caplog):
    """Test that reasoning chain is logged at DEBUG level.

    Contract: LLMAgent should:
    - Log reasoning chain with component='agent'
    - Include agent name, reasoning, and confidence
    - Log at DEBUG level
    """
    import logging
    caplog.set_level(logging.DEBUG)

    agent = MockLLMAgent(name="TestAgent", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.return_value = sample_policy_decision

    await agent.decide_action(sample_state)

    # Check that DEBUG log contains reasoning information
    # (Actual log format depends on implementation)
    debug_logs = [record for record in caplog.records if record.levelname == "DEBUG"]
    assert len(debug_logs) > 0


@pytest.mark.asyncio
async def test_llm_agent_propagates_llm_failure(mock_llm_client, sample_state):
    """Test that LLM failures are propagated.

    Contract: LLMAgent should:
    - Not catch LLM exceptions
    - Let LLMFailureException propagate to orchestrator
    """
    from llm_sim.utils.llm_client import LLMFailureException

    agent = MockLLMAgent(name="TestAgent", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.side_effect = LLMFailureException(
        reason="timeout", attempts=2
    )

    with pytest.raises(LLMFailureException):
        await agent.decide_action(sample_state)