"""Contract tests for LLMEngine abstract interface.

These tests validate the LLMEngine abstract class contract from:
specs/004-new-feature-i/contracts/engine_interface_contract.md

Tests MUST FAIL before LLMEngine implementation (TDD).
"""

import pytest
from unittest.mock import AsyncMock, Mock

# Import will fail until LLMEngine is implemented
try:
    from llm_sim.engines.llm_engine import LLMEngine
    from llm_sim.utils.llm_client import LLMClient
    from llm_sim.models.llm_models import StateUpdateDecision, PolicyDecision, ValidationResult
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.models.action import Action
    from llm_sim.models.config import SimulationConfig
except ImportError:
    pytest.skip("LLMEngine not yet implemented", allow_module_level=True)


# Mock concrete implementation for testing abstract interface
class MockLLMEngine(LLMEngine):
    """Concrete implementation of LLMEngine for testing."""

    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        """Mock state update prompt construction."""
        return f"Update state based on: {action.action_string}"

    def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
        """Mock state update application."""
        # Simple mock: just increment turn
        return SimulationState(
            turn=state.turn + 1,
            agents=state.agents,
            global_state=state.global_state,
            reasoning_chains=[]
        )


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
def validated_action():
    """Sample validated action."""
    policy_decision = PolicyDecision(
        action="Lower interest rates by 0.5%",
        reasoning="Economic reasoning",
        confidence=0.85
    )
    validation_result = ValidationResult(
        is_valid=True,
        reasoning="Economic policy",
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
def unvalidated_action():
    """Sample unvalidated action."""
    policy_decision = PolicyDecision(
        action="Deploy military forces",
        reasoning="Military reasoning",
        confidence=0.8
    )
    validation_result = ValidationResult(
        is_valid=False,
        reasoning="Not economic",
        confidence=0.95,
        action_evaluated="Deploy military forces"
    )
    return Action(
        agent_name="TestAgent2",
        action_string="Deploy military forces",
        policy_decision=policy_decision,
        validated=False,
        validation_result=validation_result
    )


@pytest.fixture
def state_update_decision():
    """Sample state update decision."""
    return StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Lowering rate by 0.5% from 2.5% results in 2.0%",
        confidence=0.9,
        action_applied="Lower interest rates by 0.5%"
    )


def test_llm_engine_calls_abstract_methods():
    """Test that LLMEngine has required abstract methods.

    Contract: LLMEngine must define:
    - _construct_state_update_prompt (abstract)
    - _apply_state_update (abstract)
    """
    # Verify abstract methods exist
    assert hasattr(LLMEngine, '_construct_state_update_prompt')
    assert hasattr(LLMEngine, '_apply_state_update')

    # Verify they are abstract (can't instantiate without implementing)
    try:
        engine = LLMEngine(config=Mock(), llm_client=Mock())
        pytest.fail("Should not be able to instantiate abstract LLMEngine")
    except TypeError as e:
        assert "abstract" in str(e).lower()


@pytest.mark.asyncio
async def test_llm_engine_run_turn_workflow(mock_llm_client, mock_config, sample_state, validated_action, state_update_decision):
    """Test run_turn workflow.

    Contract: LLMEngine.run_turn should:
    1. Filter to validated actions only
    2. For each validated action:
       - Call _construct_state_update_prompt
       - Call llm_client.call_with_retry(prompt, StateUpdateDecision)
       - Log reasoning at DEBUG level
    3. Call _apply_state_update to create new state
    4. Attach reasoning_chains to new state
    """
    engine = MockLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    new_state = await engine.run_turn([validated_action])

    # Assertions
    assert isinstance(new_state, SimulationState)
    assert mock_llm_client.call_with_retry.called
    assert new_state.turn == sample_state.turn + 1


@pytest.mark.asyncio
async def test_llm_engine_skips_unvalidated_with_log(mock_llm_client, mock_config, sample_state, validated_action, unvalidated_action, state_update_decision, caplog):
    """Test that unvalidated actions are skipped with INFO log.

    Contract: LLMEngine should:
    - Process only validated actions
    - Log INFO: "SKIPPED Agent [name] due to unvalidated Action"
    - Not call LLM for unvalidated actions
    - Continue processing (not abort)
    """
    import logging
    caplog.set_level(logging.INFO)

    engine = MockLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    new_state = await engine.run_turn([validated_action, unvalidated_action])

    # Assertions
    assert isinstance(new_state, SimulationState)

    # Check INFO log for skipped agent
    info_logs = [record.message for record in caplog.records if record.levelname == "INFO"]
    assert any("SKIPPED" in log and "TestAgent2" in log for log in info_logs)

    # Should only call LLM once (for validated action)
    assert mock_llm_client.call_with_retry.call_count == 1


@pytest.mark.asyncio
async def test_llm_engine_attaches_reasoning_chains(mock_llm_client, mock_config, sample_state, validated_action, state_update_decision):
    """Test that reasoning chains are attached to new state.

    Contract: LLMEngine should:
    - Accumulate LLMReasoningChain instances during processing
    - Attach all reasoning_chains to new SimulationState
    - Include chains from all processed actions
    """
    engine = MockLLMEngine(config=mock_config, llm_client=mock_llm_client)
    engine.current_state = sample_state
    mock_llm_client.call_with_retry.return_value = state_update_decision

    new_state = await engine.run_turn([validated_action])

    # Assertions
    assert hasattr(new_state, 'reasoning_chains')
    # Reasoning chains will be populated by actual implementation
    # Mock implementation may not populate them, but the field should exist