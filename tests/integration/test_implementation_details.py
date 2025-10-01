"""Integration tests that verify actual implementation details."""

import pytest
from pathlib import Path
from typing import List

from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState, AgentState, GlobalState
from llm_sim.models.action import Action
from llm_sim.implementations.engines.economic import EconomicEngine
from llm_sim.implementations.agents.nation import NationAgent
from llm_sim.implementations.validators.always_valid import AlwaysValidValidator


class TestActualImplementation:
    """Tests that verify actual implementation logic, not mocks."""

    def test_economic_engine_interest_calculation(self, tmp_path: Path) -> None:
        """Test that EconomicEngine correctly applies compound interest."""
        config_data = {
            "simulation": {
                "name": "Interest Test",
                "max_turns": 10,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.1},  # 10% interest
            "agents": [
                {"name": "TestNation", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        engine = EconomicEngine(config)

        # Initialize and verify initial state
        initial_state = engine.initialize_state()
        assert initial_state.agents["TestNation"].economic_strength == 1000.0
        assert initial_state.global_state.interest_rate == 0.1

        # Apply engine rules manually to verify interest calculation
        state_after_1_turn = engine.apply_engine_rules(initial_state)
        assert state_after_1_turn.agents["TestNation"].economic_strength == 1100.0  # 1000 * 1.1

        state_after_2_turns = engine.apply_engine_rules(state_after_1_turn)
        assert state_after_2_turns.agents["TestNation"].economic_strength == 1210.0  # 1100 * 1.1

        # Verify compound interest over multiple turns
        state = initial_state
        for i in range(10):
            state = engine.apply_engine_rules(state)

        expected_value = 1000 * (1.1**10)  # Compound interest formula
        assert state.agents["TestNation"].economic_strength == pytest.approx(
            expected_value, rel=1e-9
        )

    def test_nation_agent_strategy_behavior(self, tmp_path: Path) -> None:
        """Test that NationAgent returns correct actions based on strategy."""
        # Test grow strategy
        grow_agent = NationAgent(name="GrowNation", strategy="grow")
        state = SimulationState(
            turn=0,
            agents={"GrowNation": AgentState(name="GrowNation", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        grow_action = grow_agent.decide_action(state)
        assert grow_action.action_name == "grow"
        assert grow_action.agent_name == "GrowNation"
        assert grow_action.parameters["strength"] == 1000.0

        # Test maintain strategy
        maintain_agent = NationAgent(name="MaintainNation", strategy="maintain")
        state = SimulationState(
            turn=0,
            agents={
                "MaintainNation": AgentState(name="MaintainNation", economic_strength=2000.0)
            },
            global_state=GlobalState(interest_rate=0.05, total_economic_value=2000.0),
        )

        maintain_action = maintain_agent.decide_action(state)
        assert maintain_action.action_name == "maintain"
        assert maintain_action.parameters["strength"] == 2000.0

        # Test decline strategy
        decline_agent = NationAgent(name="DeclineNation", strategy="decline")
        state = SimulationState(
            turn=0,
            agents={"DeclineNation": AgentState(name="DeclineNation", economic_strength=3000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=3000.0),
        )

        decline_action = decline_agent.decide_action(state)
        assert decline_action.action_name == "decline"
        assert decline_action.parameters["strength"] == 3000.0

    def test_validator_marks_actions_correctly(self, tmp_path: Path) -> None:
        """Test that AlwaysValidValidator properly marks actions as validated."""
        validator = AlwaysValidValidator()

        state = SimulationState(
            turn=1,
            agents={"Nation": AgentState(name="Nation", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        # Create unvalidated actions
        actions = [
            Action(agent_name="Nation", action_name="grow", parameters={"value": 100}),
            Action(agent_name="Nation", action_name="maintain", parameters={"value": 200}),
        ]

        # Ensure actions are not validated initially
        assert not actions[0].validated
        assert not actions[1].validated

        # Validate actions
        validated_actions = validator.validate_actions(actions, state)

        # Check all actions are validated
        assert len(validated_actions) == 2
        for action in validated_actions:
            assert action.validated
            assert action.validation_timestamp is not None

        # Check stats are updated
        stats = validator.get_stats()
        assert stats["total_validated"] == 2
        assert stats["total_rejected"] == 0

    def test_orchestrator_integration_flow(self, tmp_path: Path) -> None:
        """Test the full orchestrator flow with real components."""
        config_data = {
            "simulation": {
                "name": "Flow Test",
                "max_turns": 3,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Nation_B", "type": "nation", "initial_economic_strength": 2000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config, output_root=tmp_path)

        # Verify components are correctly instantiated (use type name due to import issues)
        assert type(orchestrator.engine).__name__ == "EconomicEngine"
        assert len(orchestrator.agents) == 2
        assert all(type(agent).__name__ == "NationAgent" for agent in orchestrator.agents)
        assert type(orchestrator.validator).__name__ == "AlwaysValidValidator"

        # Run simulation
        result = orchestrator.run()

        # Verify history contains correct number of states
        assert len(result["history"]) == 4  # Initial + 3 turns

        # Verify each turn in history
        for i, state in enumerate(result["history"]):
            assert state.turn == i
            if i > 0:
                # Verify interest was applied (each agent should grow by 5%)
                prev_state = result["history"][i - 1]
                for agent_name in state.agents:
                    expected_strength = prev_state.agents[agent_name].economic_strength * 1.05
                    actual_strength = state.agents[agent_name].economic_strength
                    assert actual_strength == pytest.approx(expected_strength, rel=1e-9)

        # Verify final values
        final_state = result["final_state"]
        assert final_state.agents["Nation_A"].economic_strength == pytest.approx(
            1000 * (1.05**3), rel=1e-9
        )
        assert final_state.agents["Nation_B"].economic_strength == pytest.approx(
            2000 * (1.05**3), rel=1e-9
        )

    def test_termination_conditions_actually_work(self, tmp_path: Path) -> None:
        """Test that termination conditions are evaluated correctly by the engine."""
        # Test max value termination
        config_data = {
            "simulation": {
                "name": "Termination Test",
                "max_turns": 100,
                "termination": {"max_value": 1200.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.1},
            "agents": [
                {"name": "Nation", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        engine = EconomicEngine(config)

        # Test termination check
        state_below_max = SimulationState(
            turn=1,
            agents={"Nation": AgentState(name="Nation", economic_strength=1100.0)},
            global_state=GlobalState(interest_rate=0.1, total_economic_value=1100.0),
        )
        assert not engine.check_termination(state_below_max)

        state_above_max = SimulationState(
            turn=2,
            agents={"Nation": AgentState(name="Nation", economic_strength=1210.0)},
            global_state=GlobalState(interest_rate=0.1, total_economic_value=1210.0),
        )
        assert engine.check_termination(state_above_max)

    def test_state_immutability_in_practice(self, tmp_path: Path) -> None:
        """Test that states are truly immutable during simulation."""
        config_data = {
            "simulation": {
                "name": "Immutability Test",
                "max_turns": 2,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        orchestrator = SimulationOrchestrator(config, output_root=tmp_path)
        result = orchestrator.run()

        # Verify each state in history is distinct
        states = result["history"]
        for i in range(len(states)):
            for j in range(i + 1, len(states)):
                assert states[i] is not states[j]  # Different objects
                assert states[i].turn != states[j].turn  # Different turns

        # Try to modify a state (should fail)
        with pytest.raises(Exception):  # Pydantic will raise an error
            result["history"][0].turn = 999

    def test_action_parameters_passed_correctly(self, tmp_path: Path) -> None:
        """Test that action parameters are correctly passed through the system."""
        agent = NationAgent(name="TestNation", strategy="grow")

        state = SimulationState(
            turn=5,
            agents={"TestNation": AgentState(name="TestNation", economic_strength=1234.56)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1234.56),
        )

        action = agent.decide_action(state)

        # Verify the action contains the current strength as a parameter
        assert "strength" in action.parameters
        assert action.parameters["strength"] == 1234.56
        assert action.agent_name == "TestNation"
        assert action.action_name == "grow"