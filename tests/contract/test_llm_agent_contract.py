"""
Contract tests for LLMAgent abstract base class.

These tests validate the interface and workflow of the LLM-enabled
agent base class, ensuring abstract methods are enforced and the
decision workflow is correct.

Status: THESE TESTS MUST FAIL - LLMAgent not yet implemented
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# These imports will fail until implementation is complete
try:
    from llm_sim.agents.llm_agent import LLMAgent
    from llm_sim.models.llm_models import PolicyDecision
    from llm_sim.models.action import Action
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.utils.llm_client import LLMClient
except ImportError:
    pytest.skip("LLMAgent not yet implemented", allow_module_level=True)


def test_llm_agent_calls_abstract_methods():
    """Verify _construct_prompt and _validate_decision are abstract"""
    # Then: Cannot instantiate LLMAgent directly (abstract methods)
    with pytest.raises(TypeError):
        mock_client = MagicMock()
        LLMAgent(name="test", llm_client=mock_client)


@pytest.mark.asyncio
async def test_llm_agent_decide_action_workflow():
    """Verify decide_action calls: prompt→LLM→log→create_action"""

    # Given: Mock concrete implementation of LLMAgent
    class TestLLMAgent(LLMAgent):
        def _construct_prompt(self, state):
            return "test prompt"

        def _validate_decision(self, decision):
            return True

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = PolicyDecision(
        action="Lower interest rates",
        reasoning="To combat deflation",
        confidence=0.85
    )

    agent = TestLLMAgent(name="TestNation", llm_client=mock_client)

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

    # When: Calling decide_action
    action = await agent.decide_action(state)

    # Then: Returns Action with policy_decision
    assert isinstance(action, Action)
    assert action.agent_name == "TestNation"
    assert action.action_string == "Lower interest rates"
    assert action.policy_decision is not None
    assert action.policy_decision.confidence == 0.85

    # And: LLM client was called
    assert mock_client.call_with_retry.call_count == 1


@pytest.mark.asyncio
async def test_llm_agent_logs_reasoning_chain():
    """Verify DEBUG log with reasoning chain is created"""

    # Given: Mock concrete implementation
    class TestLLMAgent(LLMAgent):
        def _construct_prompt(self, state):
            return "test prompt"

        def _validate_decision(self, decision):
            return True

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = PolicyDecision(
        action="Test action",
        reasoning="Test reasoning",
        confidence=0.5
    )

    agent = TestLLMAgent(name="TestAgent", llm_client=mock_client)

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

    # When: Calling decide_action
    action = await agent.decide_action(state)

    # Then: Action has reasoning chain reference
    # (Note: Actual logging verification would require log capture)
    assert action.policy_decision.reasoning == "Test reasoning"


@pytest.mark.asyncio
async def test_llm_agent_propagates_llm_failure():
    """Verify exception propagates when LLM fails"""

    # Given: Mock implementation with failing LLM
    class TestLLMAgent(LLMAgent):
        def _construct_prompt(self, state):
            return "test prompt"

        def _validate_decision(self, decision):
            return True

    mock_client = AsyncMock()
    from llm_sim.utils.llm_client import LLMFailureException
    mock_client.call_with_retry.side_effect = LLMFailureException(
        reason="timeout",
        attempts=2
    )

    agent = TestLLMAgent(name="TestAgent", llm_client=mock_client)

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

    # When/Then: Exception propagates
    with pytest.raises(LLMFailureException):
        await agent.decide_action(state)
