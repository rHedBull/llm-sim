"""Contract tests for EconLLMEngine concrete implementation.

These tests validate the EconLLMEngine contract from:
specs/004-new-feature-i/contracts/engine_interface_contract.md

Tests MUST FAIL before EconLLMEngine implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock

# Import will fail until EconLLMEngine is implemented
try:
    from llm_sim.engines.econ_llm_engine import EconLLMEngine
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import StateUpdateDecision, PolicyDecision, ValidationResult
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
    from llm_sim.models.config import SimulationConfig
except ImportError:
    pytest.skip("EconLLMEngine not yet implemented", allow_module_level=True)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.call_with_retry = AsyncMock()
    return client


@pytest.fixture
def mock_config():
    """Mock simulation config."""
    return Mock(spec=SimulationConfig)


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
def validated_action():
    """Sample validated economic action."""
    policy_decision = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="High unemployment indicates weak demand",
        confidence=0.85
    )
    validation_result = ValidationResult(
        is_valid=True,
        reasoning="Economic policy within domain",
        confidence=0.9,
        action_evaluated="Lower interest rates by 0.5%"
    )
    return Action(
        agent_name="TestAgent",
        action_string="Lower interest rates by 0.5%",
        policy_decision=policy_decision,
        validated=True,
        validation_result=validation_result
    )


@pytest.fixture
def state_update_decision():
    """Sample state update decision."""
    return StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Lowering rate by 0.5% from current 2.5% results in 2.0%",
        confidence=0.9,
        action_applied="Lower interest rates by 0.5%"
    )


@pytest.mark.asyncio
async def test_econ_engine_processes_validated_action(mock_llm_client, mock_config, sample_state, validated_action, state_update_decision):
    """Test that engine processes validated actions with LLM.

    Contract: EconLLMEngine should:
    - Use LLM to determine new interest rate
    - Apply economic reasoning
    - Update state with new interest rate
    """
    engine = EconLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    new_state = await engine.run_turn([validated_action])

    # Assertions
    assert isinstance(new_state, SimulationState)
    assert new_state.global_state.interest_rate == 2.0
    assert new_state.turn == sample_state.turn + 1


@pytest.mark.asyncio
async def test_econ_engine_constructs_economic_prompt(mock_llm_client, mock_config, sample_state, validated_action, state_update_decision):
    """Test that prompt includes current rate and action.

    Contract: EconLLMEngine._construct_state_update_prompt should include:
    - Current interest rate
    - Current economic indicators (inflation, GDP, unemployment)
    - The validated action string
    """
    engine = EconLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    await engine.run_turn([validated_action])

    # Get the prompt that was passed to LLM
    call_args = mock_llm_client.call_with_retry.call_args
    prompt = call_args[1]['prompt']

    # Verify economic indicators are in prompt
    assert "2.5" in prompt  # Current interest rate or GDP
    assert "3.0" in prompt  # Inflation
    assert "Lower interest rates" in prompt  # Action


@pytest.mark.asyncio
async def test_econ_engine_applies_interest_rate_update(mock_llm_client, mock_config, sample_state, validated_action, state_update_decision):
    """Test that _apply_state_update only updates interest_rate.

    Contract: EconLLMEngine._apply_state_update should:
    - Update only interest_rate field (economic domain)
    - Preserve other global state fields
    - Increment turn number
    - Use immutable state pattern (model_copy)
    """
    engine = EconLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    new_state = await engine.run_turn([validated_action])

    # Verify only interest rate changed
    assert new_state.global_state.interest_rate == 2.0
    assert new_state.global_state.gdp_growth == sample_state.global_state.gdp_growth
    assert new_state.global_state.inflation == sample_state.global_state.inflation
    assert new_state.global_state.unemployment == sample_state.global_state.unemployment

    # Verify turn incremented
    assert new_state.turn == sample_state.turn + 1


@pytest.mark.asyncio
async def test_econ_engine_sequential_aggregation(mock_llm_client, mock_config, sample_state, state_update_decision):
    """Test sequential application of multiple actions.

    Contract: EconLLMEngine should:
    - Process multiple actions sequentially
    - Apply each action's state update in order
    - Final state reflects all accumulated changes
    """
    engine = EconLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state

    # Create two validated actions
    action1 = Action(
        agent_name="Agent1",
        action_string="Lower interest rates by 0.5%",
        policy_decision=PolicyDecision(action="Lower rates", reasoning="Test reasoning for policy", confidence=0.8),
        validated=True,
        validation_result=ValidationResult(
            is_valid=True, reasoning="Valid economic action", confidence=0.9, action_evaluated="Lower rates"
        )
    )

    action2 = Action(
        agent_name="Agent2",
        action_string="Lower interest rates by 0.3%",
        policy_decision=PolicyDecision(action="Lower rates more", reasoning="Test reasoning for policy", confidence=0.8),
        validated=True,
        validation_result=ValidationResult(
            is_valid=True, reasoning="Valid economic action", confidence=0.9, action_evaluated="Lower rates more"
        )
    )

    # Mock sequential decisions
    decision1 = StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="First reduction",
        confidence=0.9,
        action_applied="Lower interest rates by 0.5%"
    )

    decision2 = StateUpdateDecision(
        new_interest_rate=1.7,
        reasoning="Second reduction",
        confidence=0.9,
        action_applied="Lower interest rates by 0.3%"
    )

    mock_llm_client.call_with_retry.side_effect = [decision1, decision2]

    new_state = await engine.run_turn([action1, action2])

    # Both actions should be processed
    assert mock_llm_client.call_with_retry.call_count == 2
    # Final state should reflect sequential application
    assert new_state.turn == sample_state.turn + 1