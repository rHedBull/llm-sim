"""Contract tests for _run_async event writer integration.

These tests verify that _run_async() properly integrates with EventWriter
by calling start(), emit(), and stop() with the correct event types.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from pathlib import Path

from llm_sim.orchestrator import Orchestrator
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    AgentConfig,
    EngineConfig,
    ValidatorConfig,
)
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState


class MockAsyncAgent(BaseAgent):
    """Mock agent with async decide_action to trigger _run_async path."""

    async def decide_action(self, state: SimulationState) -> Action:
        """Async mock action."""
        return Action(
            agent_name=self.name,
            action_name="mock_action",
            parameters={},
            validated=True  # Pre-validated to avoid validator issues
        )


def make_orchestrator_fully_async(orchestrator):
    """Helper to make all orchestrator components async-compatible for testing."""
    # Make validator async
    async def async_validate(actions, state):
        return actions
    orchestrator.validator.validate_actions = async_validate

    # Make engine async
    sync_run_turn = orchestrator.engine.run_turn
    async def async_run_turn(actions):
        return sync_run_turn(actions)
    orchestrator.engine.run_turn = async_run_turn


class TestOrchestratorAsyncEventsContract:
    """Contract tests for _run_async event writer integration."""

    def test_run_async_calls_event_writer_start(self, tmp_path):
        """CONTRACT: _run_async must call event_writer.start()."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="async-test",
                max_turns=1,
                checkpoint_interval=999
            ),
            agents=[AgentConfig(name="test", type="simple", initial_state={})],
            global_state={"turn": 0},
            engine=EngineConfig(type="simple_economic"),
            validator=ValidatorConfig(type="basic")
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        orchestrator = Orchestrator(config, output_root=output_dir)
        # Replace with async agent to trigger _run_async
        orchestrator.agents = [MockAsyncAgent("test")]

        make_orchestrator_fully_async(orchestrator)

        # Mock event writer methods
        with patch.object(orchestrator.event_writer, 'start', new_callable=AsyncMock) as mock_start, \
             patch.object(orchestrator.event_writer, 'stop', new_callable=AsyncMock) as mock_stop, \
             patch.object(orchestrator.event_writer, 'emit') as mock_emit:

            orchestrator.run()

            # Verify start was called
            mock_start.assert_called_once()

    def test_run_async_emits_milestone_events(self, tmp_path):
        """CONTRACT: _run_async must emit simulation_start, turn_start, turn_end, simulation_end milestones."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="async-test",
                max_turns=2,
                checkpoint_interval=999
            ),
            agents=[AgentConfig(name="test", type="simple", initial_state={})],
            global_state={"turn": 0},
            engine=EngineConfig(type="simple_economic"),
            validator=ValidatorConfig(type="basic")
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        orchestrator = Orchestrator(config, output_root=output_dir)
        orchestrator.agents = [MockAsyncAgent("test")]
        make_orchestrator_fully_async(orchestrator)
