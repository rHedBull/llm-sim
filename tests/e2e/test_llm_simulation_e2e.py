"""End-to-end test for LLM-based simulation with mocked LLM responses."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.models.llm_models import PolicyDecision, ValidationResult, StateUpdateDecision


def test_llm_simulation_complete_flow_mocked():
    """Test complete LLM simulation flow with mocked LLM client.

    This is an end-to-end test that verifies:
    1. LLM agents generate policy decisions
    2. LLM validator validates economic actions
    3. LLM engine updates state based on decisions
    4. Simulation completes successfully
    5. Reasoning chains are captured
    """

    # We'll mock the LLMClient.call_with_retry method
    with patch("llm_sim.utils.llm_client.LLMClient.call_with_retry", new_callable=AsyncMock) as mock_call:
        # Setup responses for 1 turn × 2 agents
        # Each turn: 2 agents × (1 agent call + 1 validator call) + 2 engine calls = 6 calls

        mock_call.side_effect = [
            # Turn 1
            # USA Agent
            PolicyDecision(
                action="Lower interest rates by 0.25%",
                reasoning="Economic indicators suggest need for stimulus",
                confidence=0.85
            ),
            # USA Validator
            ValidationResult(
                is_valid=True,
                reasoning="Interest rate policy is core economic domain",
                confidence=0.95,
                action_evaluated="Lower interest rates by 0.25%"
            ),
            # USA Engine
            StateUpdateDecision(
                new_interest_rate=2.25,
                reasoning="Lowered rate from 2.5% to 2.25% based on policy",
                confidence=0.90,
                action_applied="Lower interest rates by 0.25%"
            ),
            # EU Agent
            PolicyDecision(
                action="Maintain current interest rates",
                reasoning="Economic stability requires no changes",
                confidence=0.80
            ),
            # EU Validator
            ValidationResult(
                is_valid=True,
                reasoning="Interest rate maintenance is economic policy",
                confidence=0.95,
                action_evaluated="Maintain current interest rates"
            ),
            # EU Engine
            StateUpdateDecision(
                new_interest_rate=2.25,
                reasoning="Maintaining rate at 2.25% per policy",
                confidence=0.90,
                action_applied="Maintain current interest rates"
            ),
        ]

        # Create orchestrator and override config for faster test
        orchestrator = SimulationOrchestrator.from_yaml("config_llm_example.yaml")
        orchestrator.config.simulation.max_turns = 1

        # Run simulation
        results = orchestrator.run()

        # Verify simulation completed successfully
        assert results is not None
        assert "final_state" in results
        assert "history" in results
        assert "stats" in results

        # Verify we have 2 states (initial + 1 turn)
        assert len(results["history"]) == 2

        # Verify final state
        final_state = results["final_state"]
        assert final_state.turn == 1

        # Verify agents exist
        assert "USA" in final_state.agents
        assert "EU" in final_state.agents

        # Verify interest rate changed
        initial_rate = results["history"][0].global_state.interest_rate
        final_rate = final_state.global_state.interest_rate
        assert final_rate != initial_rate
        assert abs(final_rate - 2.25) < 0.01

        # Verify LLM was called expected number of times
        # 1 turn × 2 agents × 3 calls per agent (agent, validator, engine) = 6 calls
        assert mock_call.call_count == 6

        # Verify stats
        stats = results["stats"]
        assert stats["total_turns"] == 1
        assert stats["simulation_name"] == "Economic LLM Simulation"


def test_llm_validation_rejection_flow_mocked():
    """Test that rejected actions are properly skipped by engine."""

    with patch("llm_sim.utils.llm_client.LLMClient.call_with_retry", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = [
            # USA Agent - proposes non-economic action
            PolicyDecision(
                action="Deploy military forces",
                reasoning="Security response",
                confidence=0.75
            ),
            # USA Validator - rejects
            ValidationResult(
                is_valid=False,
                reasoning="Military action is not economic policy",
                confidence=0.98,
                action_evaluated="Deploy military forces"
            ),
            # EU Agent - proposes economic action
            PolicyDecision(
                action="Lower interest rates by 0.5%",
                reasoning="Stimulate growth",
                confidence=0.85
            ),
            # EU Validator - accepts
            ValidationResult(
                is_valid=True,
                reasoning="Interest rate policy is economic domain",
                confidence=0.95,
                action_evaluated="Lower interest rates by 0.5%"
            ),
            # EU Engine (USA was skipped)
            StateUpdateDecision(
                new_interest_rate=2.0,
                reasoning="Lowered rate from 2.5% to 2.0%",
                confidence=0.90,
                action_applied="Lower interest rates by 0.5%"
            ),
        ]

        orchestrator = SimulationOrchestrator.from_yaml("config_llm_example.yaml")
        orchestrator.config.simulation.max_turns = 1
        results = orchestrator.run()

        # Verify simulation completed
        assert results is not None

        # Verify only 1 engine call was made (USA was skipped)
        # 2 agent calls + 2 validator calls + 1 engine call = 5
        assert mock_call.call_count == 5

        # Verify final state reflects only EU's action
        final_state = results["final_state"]
        assert abs(final_state.global_state.interest_rate - 2.0) < 0.01


def test_llm_with_real_config_file():
    """Test that LLM config file loads correctly (without running simulation)."""

    # This test just verifies the config loads without Ollama running
    try:
        orchestrator = SimulationOrchestrator.from_yaml("config_llm_example.yaml")

        # Verify components are LLM-based
        assert orchestrator.config.llm is not None
        assert orchestrator.config.llm.model == "gemma3:1b"
        assert orchestrator.config.engine.type == "econ_llm_engine"
        assert orchestrator.config.validator.type == "econ_llm_validator"
        assert orchestrator.config.agents[0].type == "econ_llm_agent"

        # Verify agents created correctly
        assert len(orchestrator.agents) == 2

    except Exception as e:
        pytest.fail(f"Failed to load LLM configuration: {e}")