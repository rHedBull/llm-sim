"""Contract tests for EconLLMAgent concrete implementation.

These tests validate the EconLLMAgent contract from:
specs/004-new-feature-i/contracts/agent_interface_contract.md

Tests MUST FAIL before EconLLMAgent implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock

# Import will fail until EconLLMAgent is implemented
try:
    from llm_sim.agents.econ_llm_agent import EconLLMAgent
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import PolicyDecision
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
except ImportError:
    pytest.skip("EconLLMAgent not yet implemented", allow_module_level=True)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.call_with_retry = AsyncMock()
    return client


@pytest.fixture
def sample_state():
    """Sample simulation state with economic indicators."""
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
def economic_policy_decision():
    """Sample economic policy decision."""
    return PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="High unemployment at 5.0% indicates weak demand. Lowering rates can stimulate borrowing.",
        confidence=0.85
    )


@pytest.mark.asyncio
async def test_econ_agent_generates_policy_with_llm(mock_llm_client, sample_state, economic_policy_decision):
    """Test that EconLLMAgent generates policy using LLM.

    Contract: EconLLMAgent should:
    - Use LLM to generate PolicyDecision
    - Create Action with action_string (not action_type enum)
    - Include policy_decision in Action
    """
    agent = EconLLMAgent(name="TestNation", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.return_value = economic_policy_decision

    action = await agent.decide_action(sample_state)

    # Assertions
    assert isinstance(action, Action)
    assert action.agent_name == "TestNation"
    assert action.action_string == "Lower interest rates by 0.5%"
    assert action.policy_decision == economic_policy_decision
    assert action.policy_decision.confidence == 0.85


@pytest.mark.asyncio
async def test_econ_agent_constructs_economic_prompt(mock_llm_client, sample_state, economic_policy_decision):
    """Test that prompt includes all economic indicators.

    Contract: EconLLMAgent._construct_prompt should include:
    - GDP growth
    - Inflation
    - Unemployment
    - Interest rate
    """
    agent = EconLLMAgent(name="TestNation", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.return_value = economic_policy_decision

    await agent.decide_action(sample_state)

    # Get the prompt that was passed to LLM
    call_args = mock_llm_client.call_with_retry.call_args
    prompt = call_args[1]['prompt']

    # Verify economic indicators are in prompt
    assert "2.5" in prompt  # GDP or interest rate
    assert "3.0" in prompt  # Inflation
    assert "5.0" in prompt  # Unemployment


@pytest.mark.asyncio
async def test_econ_agent_validates_economic_keywords(mock_llm_client, sample_state):
    """Test that _validate_decision checks for economic keywords.

    Contract: EconLLMAgent._validate_decision should:
    - Accept actions with economic keywords (rate, fiscal, tax, trade, monetary, interest)
    - Reject actions without economic keywords
    """
    agent = EconLLMAgent(name="TestNation", llm_client=mock_llm_client)

    # Test with economic action
    economic_decision = PolicyDecision(
        action="Adjust interest rates",
        reasoning="Economic reasoning",
        confidence=0.8
    )
    assert agent._validate_decision(economic_decision) is True

    # Test with non-economic action
    non_economic_decision = PolicyDecision(
        action="Deploy military forces",
        reasoning="Military reasoning",
        confidence=0.8
    )
    assert agent._validate_decision(non_economic_decision) is False


@pytest.mark.asyncio
async def test_econ_agent_flexible_action_string(mock_llm_client, sample_state):
    """Test that action is flexible string, not enum.

    Contract: EconLLMAgent should:
    - Accept any action string from LLM
    - Not constrain to predefined ActionType enum
    - Allow creative policy descriptions
    """
    creative_decision = PolicyDecision(
        action="Implement quantitative easing program targeting corporate bonds",
        reasoning="Unconventional monetary policy to address credit market dysfunction",
        confidence=0.7
    )

    agent = EconLLMAgent(name="TestNation", llm_client=mock_llm_client)
    mock_llm_client.call_with_retry.return_value = creative_decision

    action = await agent.decide_action(sample_state)

    # Should accept creative/flexible action string
    assert action.action_string == "Implement quantitative easing program targeting corporate bonds"
    assert hasattr(action, 'action_string')  # Not action_type enum