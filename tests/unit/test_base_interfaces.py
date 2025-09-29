"""Tests for base interfaces."""

import pytest
from typing import List

from src.llm_sim.models.state import SimulationState, AgentState, GlobalState
from src.llm_sim.models.action import Action, ActionType
from src.llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    TerminationConditions,
    EngineConfig,
    ValidatorConfig,
    LoggingConfig,
)
from src.llm_sim.engines.base import BaseEngine
from src.llm_sim.agents.base import BaseAgent
from src.llm_sim.validators.base import BaseValidator


class TestBaseEngine:
    """Tests for BaseEngine abstract class."""

    def test_abstract_methods_defined(self) -> None:
        """Test that abstract methods are properly defined."""
        assert hasattr(BaseEngine, "initialize_state")
        assert hasattr(BaseEngine, "apply_actions")
        assert hasattr(BaseEngine, "apply_engine_rules")
        assert hasattr(BaseEngine, "check_termination")
        assert hasattr(BaseEngine, "get_current_state")
        assert hasattr(BaseEngine, "run_turn")

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that abstract class cannot be instantiated."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="test", interest_rate=0.05),
            agents=[],
            validator=ValidatorConfig(type="test"),
            logging=LoggingConfig(),
        )

        with pytest.raises(TypeError):
            BaseEngine(config)  # type: ignore

    def test_concrete_implementation(self) -> None:
        """Test that concrete implementation works."""

        class TestEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                agents = {"Test": AgentState(name="Test", economic_strength=1000.0)}
                return SimulationState(
                    turn=0,
                    agents=agents,
                    global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
                )

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state  # type: ignore

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return state.turn >= self.config.simulation.max_turns

        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="test", interest_rate=0.05),
            agents=[],
            validator=ValidatorConfig(type="test"),
            logging=LoggingConfig(),
        )

        engine = TestEngine(config)
        state = engine.initialize_state()
        assert state.turn == 0
        assert "Test" in state.agents

    def test_get_current_state_before_init(self) -> None:
        """Test that get_current_state raises error if not initialized."""

        class TestEngine(BaseEngine):
            def initialize_state(self) -> SimulationState:
                return SimulationState(
                    turn=0,
                    agents={},
                    global_state=GlobalState(interest_rate=0, total_economic_value=0),
                )

            def apply_actions(self, actions: List[Action]) -> SimulationState:
                return self._state  # type: ignore

            def apply_engine_rules(self, state: SimulationState) -> SimulationState:
                return state

            def check_termination(self, state: SimulationState) -> bool:
                return False

        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="test", interest_rate=0.05),
            agents=[],
            validator=ValidatorConfig(type="test"),
            logging=LoggingConfig(),
        )

        engine = TestEngine(config)
        with pytest.raises(RuntimeError, match="not initialized"):
            engine.get_current_state()


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    def test_abstract_methods_defined(self) -> None:
        """Test that abstract methods are properly defined."""
        assert hasattr(BaseAgent, "decide_action")
        assert hasattr(BaseAgent, "receive_state")
        assert hasattr(BaseAgent, "get_current_state")

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseAgent("Test")  # type: ignore

    def test_concrete_implementation(self) -> None:
        """Test that concrete implementation works."""

        class TestAgent(BaseAgent):
            def decide_action(self, state: SimulationState) -> Action:
                return Action(
                    agent_name=self.name,
                    action_type=ActionType.GROW,
                    parameters={},
                )

        agent = TestAgent("TestAgent")
        assert agent.name == "TestAgent"
        assert agent.get_current_state() is None

        state = SimulationState(
            turn=0,
            agents={"TestAgent": AgentState(name="TestAgent", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        agent.receive_state(state)
        assert agent.get_current_state() == state

        action = agent.decide_action(state)
        assert action.agent_name == "TestAgent"
        assert action.action_type == ActionType.GROW


class TestBaseValidator:
    """Tests for BaseValidator abstract class."""

    def test_abstract_methods_defined(self) -> None:
        """Test that abstract methods are properly defined."""
        assert hasattr(BaseValidator, "validate_action")
        assert hasattr(BaseValidator, "validate_actions")
        assert hasattr(BaseValidator, "get_stats")

    def test_cannot_instantiate_abstract(self) -> None:
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseValidator()  # type: ignore

    def test_concrete_implementation(self) -> None:
        """Test that concrete implementation works."""

        class TestValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return True

        validator = TestValidator()
        assert validator.validation_count == 0
        assert validator.rejection_count == 0

        state = SimulationState(
            turn=0,
            agents={"Test": AgentState(name="Test", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        action = Action(agent_name="Test", action_type=ActionType.GROW, parameters={})

        assert validator.validate_action(action, state)

        actions = [action]
        validated = validator.validate_actions(actions, state)
        assert len(validated) == 1
        assert validated[0].validated
        assert validator.validation_count == 1
        assert validator.rejection_count == 0

        stats = validator.get_stats()
        assert stats["total_validated"] == 1
        assert stats["total_rejected"] == 0
        assert stats["acceptance_rate"] == 1.0

    def test_rejection_stats(self) -> None:
        """Test that rejection stats work correctly."""

        class TestValidator(BaseValidator):
            def validate_action(self, action: Action, state: SimulationState) -> bool:
                return action.agent_name != "Reject"

        validator = TestValidator()
        state = SimulationState(
            turn=0,
            agents={"Test": AgentState(name="Test", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        actions = [
            Action(agent_name="Test", action_type=ActionType.GROW, parameters={}),
            Action(agent_name="Reject", action_type=ActionType.GROW, parameters={}),
        ]

        validated = validator.validate_actions(actions, state)
        assert len(validated) == 1
        assert validated[0].agent_name == "Test"
        assert validator.validation_count == 1
        assert validator.rejection_count == 1

        stats = validator.get_stats()
        assert stats["acceptance_rate"] == 0.5
