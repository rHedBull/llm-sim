"""
Contract tests for EconLLMEngine concrete implementation.

These tests validate the economic domain-specific state update logic,
including interest rate calculations and prompt construction.

Status: THESE TESTS MUST FAIL - EconLLMEngine not yet implemented
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# These imports will fail until implementation is complete
try:
    from llm_sim.engines.econ_llm_engine import EconLLMEngine
    from llm_sim.models.llm_models import StateUpdateDecision
    from llm_sim.models.action import Action
    from llm_sim.models.state import SimulationState, GlobalState
except ImportError:
    pytest.skip("EconLLMEngine not yet implemented", allow_module_level=True)


@pytest.mark.asyncio
async def test_econ_engine_processes_validated_action():
    """Verify engine updates state based on LLM decision"""
    # Given: Mock LLM returning new interest rate
    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Lowered rate from 2.5% to 2.0% to stimulate economy",
        confidence=0.88,
        action_applied="Lower interest rates"
    )

    mock_config = MagicMock()
    engine = EconLLMEngine(config=mock_config, llm_client=mock_client)

    initial_state = SimulationState(
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
    engine.current_state = initial_state

    actions = [
        Action(agent_name="USA", action_string="Lower interest rates", validated=True)
    ]

    # When: Running turn
    new_state = await engine.run_turn(actions)

    # Then: State updated with new interest rate
    assert new_state.global_state.interest_rate == 2.0
    assert new_state.turn == 2


def test_econ_engine_constructs_economic_prompt():
    """Verify prompt includes current rate and action"""
    # Given: EconLLMEngine
    mock_client = AsyncMock()
    mock_config = MagicMock()
    engine = EconLLMEngine(config=mock_config, llm_client=mock_client)

    action = Action(
        agent_name="USA",
        action_string="Lower interest rates by 0.5%",
        validated=True
    )

    state = GlobalState(
        gdp_growth=2.5,
        inflation=3.0,
        unemployment=5.0,
        interest_rate=2.5
    )

    # When: Constructing prompt
    prompt = engine._construct_state_update_prompt(action, state)

    # Then: Prompt includes current rate and action
    assert "2.5" in prompt or "interest" in prompt.lower()
    assert "Lower interest rates" in prompt or action.action_string in prompt


def test_econ_engine_applies_interest_rate_update():
    """Verify _apply_state_update only updates interest_rate field"""
    # Given: EconLLMEngine
    mock_client = AsyncMock()
    mock_config = MagicMock()
    engine = EconLLMEngine(config=mock_config, llm_client=mock_client)

    decision = StateUpdateDecision(
        new_interest_rate=1.5,
        reasoning="Updated rate",
        confidence=0.9,
        action_applied="action"
    )

    old_state = SimulationState(
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

    # When: Applying state update
    new_state = engine._apply_state_update(decision, old_state)

    # Then: Only interest_rate changed
    assert new_state.global_state.interest_rate == 1.5
    assert new_state.global_state.gdp_growth == 2.5  # unchanged
    assert new_state.global_state.inflation == 3.0  # unchanged
    assert new_state.global_state.unemployment == 5.0  # unchanged


@pytest.mark.asyncio
async def test_econ_engine_sequential_aggregation():
    """Verify multiple actions applied sequentially"""
    # Given: Mock LLM with sequential responses
    mock_client = AsyncMock()
    mock_client.call_with_retry.side_effect = [
        StateUpdateDecision(
            new_interest_rate=2.0,
            reasoning="First action lowers rate to 2.0%",
            confidence=0.85,
            action_applied="action1"
        ),
        StateUpdateDecision(
            new_interest_rate=1.8,
            reasoning="Second action further lowers to 1.8%",
            confidence=0.80,
            action_applied="action2"
        )
    ]

    mock_config = MagicMock()
    engine = EconLLMEngine(config=mock_config, llm_client=mock_client)

    initial_state = SimulationState(
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
    engine.current_state = initial_state

    actions = [
        Action(agent_name="Agent1", action_string="action1", validated=True),
        Action(agent_name="Agent2", action_string="action2", validated=True)
    ]

    # When: Running turn with multiple actions
    new_state = await engine.run_turn(actions)

    # Then: Final rate reflects sequential application
    assert new_state.global_state.interest_rate == 1.8
    assert mock_client.call_with_retry.call_count == 2
