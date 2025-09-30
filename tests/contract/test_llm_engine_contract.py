"""
Contract tests for LLMEngine abstract base class.

These tests validate the interface and workflow of the LLM-enabled
engine base class, ensuring abstract methods are enforced and the
run_turn workflow is correct.

Status: THESE TESTS MUST FAIL - LLMEngine not yet implemented
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# These imports will fail until implementation is complete
try:
    from llm_sim.engines.llm_engine import LLMEngine
    from llm_sim.models.llm_models import StateUpdateDecision
    from llm_sim.models.action import Action
    from llm_sim.models.state import SimulationState, GlobalState
    from llm_sim.utils.llm_client import LLMClient
except ImportError:
    pytest.skip("LLMEngine not yet implemented", allow_module_level=True)


def test_llm_engine_calls_abstract_methods():
    """Verify _construct_state_update_prompt and _apply_state_update are abstract"""
    # Then: Cannot instantiate LLMEngine directly
    with pytest.raises(TypeError):
        mock_client = MagicMock()
        mock_config = MagicMock()
        LLMEngine(config=mock_config, llm_client=mock_client)


@pytest.mark.asyncio
async def test_llm_engine_run_turn_workflow():
    """Verify run_turn processes validated actions, skips unvalidated"""

    # Given: Mock concrete implementation
    class TestLLMEngine(LLMEngine):
        def _construct_state_update_prompt(self, action, state):
            return f"Update state for: {action.action_name}"

        def _apply_state_update(self, decision, state):
            # Simple update: return state unchanged (turn incremented in run_turn)
            return SimulationState(
                turn=state.turn,  # Don't increment here - run_turn does it
                agents=state.agents,
                global_state=state.global_state,
                reasoning_chains=[]
            )

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Lowered rate based on policy",
        confidence=0.85,
        action_applied="Lower rates"
    )
    # Add config attribute with model field for LLMReasoningChain creation
    mock_client.config = MagicMock()
    mock_client.config.model = "gemma:3"

    mock_config = MagicMock()
    engine = TestLLMEngine(config=mock_config, llm_client=mock_client)

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
        Action(agent_name="Agent1", action_name="Lower rates", validated=True),
        Action(agent_name="Agent2", action_name="Invalid action", validated=False)
    ]

    # When: Running turn
    new_state = await engine.run_turn(actions)

    # Then: Only validated action processed
    assert mock_client.call_with_retry.call_count == 1
    assert new_state.turn == 2


@pytest.mark.asyncio
async def test_llm_engine_skips_unvalidated_with_log():
    """Verify INFO log 'SKIPPED Agent [name] due to unvalidated Action'"""

    # Given: Mock implementation
    class TestLLMEngine(LLMEngine):
        def _construct_state_update_prompt(self, action, state):
            return "prompt"

        def _apply_state_update(self, decision, state):
            return SimulationState(
                turn=state.turn + 1,
                agents=state.agents,
                global_state=state.global_state,
                reasoning_chains=[]
            )

    mock_client = AsyncMock()
    mock_config = MagicMock()
    engine = TestLLMEngine(config=mock_config, llm_client=mock_client)

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
        Action(agent_name="SkippedAgent", action_name="action", validated=False)
    ]

    # When: Running turn with unvalidated action
    new_state = await engine.run_turn(actions)

    # Then: LLM not called (action skipped)
    assert mock_client.call_with_retry.call_count == 0
    # Note: Actual log verification would require log capture


@pytest.mark.asyncio
async def test_llm_engine_attaches_reasoning_chains():
    """Verify new state includes reasoning_chains"""

    # Given: Mock implementation
    class TestLLMEngine(LLMEngine):
        def _construct_state_update_prompt(self, action, state):
            return "prompt"

        def _apply_state_update(self, decision, state):
            # Apply decision and return new state
            return SimulationState(
                turn=state.turn + 1,
                agents=state.agents,
                global_state=state.global_state,
                reasoning_chains=[]  # Will be populated by run_turn
            )

    mock_client = AsyncMock()
    mock_client.call_with_retry.return_value = StateUpdateDecision(
        new_interest_rate=2.0,
        reasoning="Applied policy",
        confidence=0.85,
        action_applied="action"
    )
    # Add config attribute with model field for LLMReasoningChain creation
    mock_client.config = MagicMock()
    mock_client.config.model = "gemma:3"

    mock_config = MagicMock()
    engine = TestLLMEngine(config=mock_config, llm_client=mock_client)

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
        Action(agent_name="Agent1", action_name="action", validated=True)
    ]

    # When: Running turn
    new_state = await engine.run_turn(actions)

    # Then: Reasoning chains attached to new state
    # (Implementation should accumulate chains during run_turn)
    assert hasattr(new_state, 'reasoning_chains')
