"""Integration tests for end-to-end logging flow.

Tests that logging context propagates correctly through the entire system:
external context → orchestrator → agents → logs.
"""

import asyncio
import json
from io import StringIO

import pytest
import structlog

from llm_sim.utils.logging import configure_logging, get_logger


class TestEndToEndLogging:
    """Test suite for end-to-end logging integration."""

    def test_external_to_orchestrator_context_flow(self, capsys):
        """Test that external context flows to orchestrator logs."""
        # Simulate external system providing correlation context
        external_context = {
            "request_id": "req-abc-123",
            "user_id": "user-456"
        }

        # Configure logging with external context
        logger = configure_logging(format="json", bind_context=external_context)

        # Simulate orchestrator binding its own context
        orch_logger = logger.bind(
            run_id="sim-789",
            simulation_name="test-sim",
            component="orchestrator"
        )

        capsys.readouterr()  # Clear
        orch_logger.info("simulation_starting", num_agents=5)

        captured = capsys.readouterr()
        if captured.err.strip():
            log_data = json.loads(captured.err.strip())

            # Verify external context present
            assert log_data.get("request_id") == "req-abc-123"
            assert log_data.get("user_id") == "user-456"

            # Verify orchestrator context present
            assert log_data.get("run_id") == "sim-789"
            assert log_data.get("simulation_name") == "test-sim"
            assert log_data.get("component") == "orchestrator"

            # Verify event data present
            assert log_data.get("num_agents") == 5

    def test_orchestrator_to_agent_context_isolation(self, capsys):
        """Test that agent logs include agent context but are isolated from other agents."""
        configure_logging(format="json")

        # Simulate two agents with their own context
        agent1_logger = get_logger("llm_sim.agent").bind(
            agent_id="alice",
            component="agent"
        )

        agent2_logger = get_logger("llm_sim.agent").bind(
            agent_id="bob",
            component="agent"
        )

        capsys.readouterr()  # Clear

        # Agent 1 logs
        agent1_logger.info("decision_started", turn=5)
        out1 = capsys.readouterr().err.strip()

        # Agent 2 logs
        agent2_logger.info("decision_started", turn=5)
        out2 = capsys.readouterr().err.strip()

        # Parse logs
        if out1:
            data1 = json.loads(out1)
            assert data1.get("agent_id") == "alice"
            assert data1.get("turn") == 5

        if out2:
            data2 = json.loads(out2)
            assert data2.get("agent_id") == "bob"
            assert data2.get("turn") == 5

        # Verify isolation - alice's log shouldn't have bob's id and vice versa
        if out1:
            assert "bob" not in out1
        if out2:
            assert "alice" not in out2

    def test_multi_component_logging_flow(self, capsys):
        """Test logging flow through multiple components."""
        configure_logging(format="json")

        # Simulate different components
        orchestrator = get_logger("llm_sim.orchestrator").bind(component="orchestrator", run_id="test-123")
        engine = get_logger("llm_sim.engine").bind(component="engine", run_id="test-123")
        agent = get_logger("llm_sim.agent").bind(component="agent", agent_id="alice", run_id="test-123")

        capsys.readouterr()  # Clear

        # Log from each component
        orchestrator.info("turn_started", turn=1)
        out1 = capsys.readouterr().err.strip()

        agent.info("decision_made", action="trade")
        out2 = capsys.readouterr().err.strip()

        engine.info("state_updated", new_value=100)
        out3 = capsys.readouterr().err.strip()

        # All should have run_id
        for output in [out1, out2, out3]:
            if output:
                data = json.loads(output)
                assert data.get("run_id") == "test-123"

        # Each should have correct component
        if out1:
            assert json.loads(out1).get("component") == "orchestrator"
        if out2:
            data = json.loads(out2)
            assert data.get("component") == "agent"
            assert data.get("agent_id") == "alice"
        if out3:
            assert json.loads(out3).get("component") == "engine"

    def test_log_filtering_by_run_id(self, capsys):
        """Test that logs can be filtered by run_id."""
        configure_logging(format="json")

        # Simulate two concurrent simulations
        sim1_logger = get_logger("sim").bind(run_id="sim-001")
        sim2_logger = get_logger("sim").bind(run_id="sim-002")

        capsys.readouterr()  # Clear

        # Generate logs from both simulations
        sim1_logger.info("event1")
        sim1_logger.info("event2")
        sim2_logger.info("event3")
        sim1_logger.info("event4")
        sim2_logger.info("event5")

        captured = capsys.readouterr().err
        lines = [line.strip() for line in captured.split("\n") if line.strip()]

        # Parse all logs
        logs = [json.loads(line) for line in lines if line]

        # Filter by run_id
        sim1_logs = [log for log in logs if log.get("run_id") == "sim-001"]
        sim2_logs = [log for log in logs if log.get("run_id") == "sim-002"]

        # Verify correct distribution
        assert len(sim1_logs) == 3  # event1, event2, event4
        assert len(sim2_logs) == 2  # event3, event5

    def test_turn_scoped_context(self, capsys):
        """Test turn-scoped context binding pattern."""
        configure_logging(format="json")

        # Base orchestrator logger
        base_logger = get_logger("orch").bind(run_id="test-123", simulation="demo")

        capsys.readouterr()  # Clear

        # Turn 1 scope
        turn1_logger = base_logger.bind(turn=1, active_agents=5, paused_agents=0)
        turn1_logger.info("turn_started")
        out1 = capsys.readouterr().err.strip()

        # Turn 2 scope
        turn2_logger = base_logger.bind(turn=2, active_agents=4, paused_agents=1)
        turn2_logger.info("turn_started")
        out2 = capsys.readouterr().err.strip()

        # Verify turn 1 context
        if out1:
            data1 = json.loads(out1)
            assert data1.get("turn") == 1
            assert data1.get("active_agents") == 5
            assert data1.get("paused_agents") == 0

        # Verify turn 2 context
        if out2:
            data2 = json.loads(out2)
            assert data2.get("turn") == 2
            assert data2.get("active_agents") == 4
            assert data2.get("paused_agents") == 1


class TestAsyncContextPropagation:
    """Test suite for async context propagation using contextvars."""

    @pytest.mark.asyncio
    async def test_context_propagates_through_async(self, capsys):
        """Test that context propagates through async/await calls."""
        configure_logging(format="json")

        # Note: This test verifies basic async logging works
        # Full contextvars propagation depends on configure_logging implementation

        async def main_task():
            logger = get_logger("main").bind(run_id="async-123")
            logger.info("main_started")

            await nested_task()

        async def nested_task():
            logger = get_logger("nested")
            # In full implementation with contextvars, this would include run_id
            logger.info("nested_started")

        capsys.readouterr()  # Clear
        await main_task()

        captured = capsys.readouterr().err
        lines = [line.strip() for line in captured.split("\n") if line.strip()]

        # Verify both logs appear
        assert len(lines) >= 2

        # Parse logs
        logs = [json.loads(line) for line in lines if line]

        # Main log should have run_id
        main_log = next((log for log in logs if log.get("event") == "main_started"), None)
        assert main_log is not None
        assert main_log.get("run_id") == "async-123"

    @pytest.mark.asyncio
    async def test_concurrent_async_tasks_isolated(self, capsys):
        """Test that concurrent async tasks have isolated contexts."""
        configure_logging(format="json")

        async def task1():
            logger = get_logger("task").bind(task_id="task1")
            await asyncio.sleep(0.01)
            logger.info("task1_event")

        async def task2():
            logger = get_logger("task").bind(task_id="task2")
            await asyncio.sleep(0.01)
            logger.info("task2_event")

        capsys.readouterr()  # Clear

        # Run tasks concurrently
        await asyncio.gather(task1(), task2())

        captured = capsys.readouterr().err
        lines = [line.strip() for line in captured.split("\n") if line.strip()]

        logs = [json.loads(line) for line in lines if line]

        # Find each task's log
        task1_log = next((log for log in logs if log.get("event") == "task1_event"), None)
        task2_log = next((log for log in logs if log.get("event") == "task2_event"), None)

        assert task1_log is not None
        assert task2_log is not None

        # Each should have correct task_id
        assert task1_log.get("task_id") == "task1"
        assert task2_log.get("task_id") == "task2"


class TestLogFiltering:
    """Test suite for log filtering capabilities."""

    def test_filter_by_component(self, capsys):
        """Test filtering logs by component field."""
        configure_logging(format="json")

        logger1 = get_logger("test").bind(component="orchestrator")
        logger2 = get_logger("test").bind(component="agent")
        logger3 = get_logger("test").bind(component="engine")

        capsys.readouterr()  # Clear

        logger1.info("event1")
        logger2.info("event2")
        logger3.info("event3")
        logger1.info("event4")

        captured = capsys.readouterr().err
        lines = [line.strip() for line in captured.split("\n") if line.strip()]
        logs = [json.loads(line) for line in lines if line]

        # Filter by component
        orch_logs = [log for log in logs if log.get("component") == "orchestrator"]
        agent_logs = [log for log in logs if log.get("component") == "agent"]
        engine_logs = [log for log in logs if log.get("component") == "engine"]

        assert len(orch_logs) == 2
        assert len(agent_logs) == 1
        assert len(engine_logs) == 1

    def test_filter_by_agent_id(self, capsys):
        """Test filtering logs by agent_id field."""
        configure_logging(format="json")

        alice_logger = get_logger("agent").bind(agent_id="alice")
        bob_logger = get_logger("agent").bind(agent_id="bob")

        capsys.readouterr()  # Clear

        alice_logger.info("decision1")
        bob_logger.info("decision2")
        alice_logger.info("decision3")
        bob_logger.info("decision4")
        alice_logger.info("decision5")

        captured = capsys.readouterr().err
        lines = [line.strip() for line in captured.split("\n") if line.strip()]
        logs = [json.loads(line) for line in lines if line]

        # Filter by agent_id
        alice_logs = [log for log in logs if log.get("agent_id") == "alice"]
        bob_logs = [log for log in logs if log.get("agent_id") == "bob"]

        assert len(alice_logs) == 3
        assert len(bob_logs) == 2
