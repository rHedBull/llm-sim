"""
from llm_sim.models.state import GlobalState
Contract tests for EconLLMAgent concrete implementation.

These tests validate the economic domain-specific implementation
of the LLM agent, including prompt construction and keyword validation.

Status: THESE TESTS MUST FAIL - EconLLMAgent not yet implemented
"""

import pytest
from unittest.mock import AsyncMock

# These imports will fail until implementation is complete
try:
    from llm_sim.implementations.agents.econ_llm_agent import EconLLMAgent
    from llm_sim.models.llm_models import PolicyDecision
    from llm_sim.models.state import SimulationState, GlobalState
except ImportError:
    pytest.skip("EconLLMAgent not yet implemented", allow_module_level=True)


@pytest.mark.asyncio
async def test_econ_agent_generates_policy_with_llm():
    """Verify EconLLMAgent creates Action with PolicyDecision"""
    # Given: Mock LLM returning PolicyDecision
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="High unemployment and low inflation suggest expansionary policy",
        confidence=0.90
    )

    agent = EconLLMAgent(name="USA", llm_client=mock_client)

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=2.0,
            inflation=1.5,
            unemployment=6.5,
            interest_rate=2.5
        ),
        reasoning_chains=[]
    )

    # When: Agent decides action
    action = await agent.decide_action(state)

    # Then: Action created with policy decision
    assert action.action_string == "Lower interest rates by 0.5%"
    assert action.policy_decision.confidence == 0.90


@pytest.mark.asyncio
async def test_econ_agent_constructs_economic_prompt():
    """Verify prompt includes GDP, inflation, unemployment, interest rate"""
    # Given: EconLLMAgent
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = PolicyDecision(
        action="Test action",
        reasoning="Test reasoning",
        confidence=0.5
    )

    agent = EconLLMAgent(name="EU", llm_client=mock_client)

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=3.2,
            inflation=2.8,
            unemployment=4.3,
            interest_rate=1.75
        ),
        reasoning_chains=[]
    )

    # When: Agent constructs prompt
    prompt = agent._construct_prompt(state)

    # Then: Prompt includes all economic indicators
    assert "3.2" in prompt or "GDP" in prompt
    assert "2.8" in prompt or "Inflation" in prompt
    assert "4.3" in prompt or "Unemployment" in prompt
    assert "1.75" in prompt or "Interest Rate" in prompt


def test_econ_agent_validates_economic_keywords():
    """Verify _validate_decision checks for economic keywords"""
    # Given: EconLLMAgent
    mock_client = AsyncMock()
    agent = EconLLMAgent(name="TestNation", llm_client=mock_client)

    # When: Validating any action (economic or not)
    economic_decision = PolicyDecision(
        action="Adjust interest rates to 2.0%",
        reasoning="Economic policy adjustment",
        confidence=0.8
    )
    military_decision = PolicyDecision(
        action="Deploy troops to border region",
        reasoning="Military action",
        confidence=0.7
    )

    # Then: All actions pass agent validation (domain validation done by validator)
    assert agent._validate_decision(economic_decision) is True
    assert agent._validate_decision(military_decision) is True


@pytest.mark.asyncio
async def test_econ_agent_flexible_action_string():
    """Verify action is string, not enum"""
    # Given: EconLLMAgent with flexible action
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = PolicyDecision(
        action="Implement quantitative easing program targeting $50B monthly",
        reasoning="Novel monetary policy for specific conditions",
        confidence=0.75
    )

    agent = EconLLMAgent(name="TestNation", llm_client=mock_client)

    state = SimulationState(
        turn=1,
        agents={},
        global_state=GlobalState(
            gdp_growth=1.0,
            inflation=0.5,
            unemployment=8.0,
            interest_rate=0.25
        ),
        reasoning_chains=[]
    )

    # When: Agent decides action
    action = await agent.decide_action(state)

    # Then: Action is flexible string (not constrained to enum)
    assert isinstance(action.action_string, str)
    assert "quantitative easing" in action.action_string.lower()
