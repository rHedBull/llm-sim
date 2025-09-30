"""Tests for data models."""

import pytest
from datetime import datetime

from pydantic import ValidationError

from llm_sim.models.state import SimulationState, AgentState, GlobalState
from llm_sim.models.action import Action, ActionType
from llm_sim.models.config import (
    SimulationConfig,
)


class TestSimulationConfig:
    """Tests for SimulationConfig model."""

    def test_valid_config(self) -> None:
        """Test creating a valid configuration."""
        config_data = {
            "simulation": {
                "name": "Test Sim",
                "max_turns": 100,
                "termination": {"min_value": 0.0, "max_value": 1000000.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Nation_B", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)
        assert config.simulation.name == "Test Sim"
        assert config.simulation.max_turns == 100
        assert config.engine.interest_rate == 0.05
        assert len(config.agents) == 2
        assert config.agents[0].name == "Nation_A"

    def test_invalid_max_turns(self) -> None:
        """Test that negative max_turns raises error."""
        config_data = {
            "simulation": {
                "name": "Test",
                "max_turns": -1,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [],
            "validator": {"type": "always_valid"},
            "logging": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(**config_data)
        assert "max_turns" in str(exc_info.value)

    def test_invalid_interest_rate(self) -> None:
        """Test that interest rate outside bounds raises error."""
        config_data = {
            "simulation": {
                "name": "Test",
                "max_turns": 10,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 2.0},  # > 1.0
            "agents": [],
            "validator": {"type": "always_valid"},
            "logging": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(**config_data)
        assert "interest_rate" in str(exc_info.value)

    def test_duplicate_agent_names(self) -> None:
        """Test that duplicate agent names raise error."""
        config_data = {
            "simulation": {
                "name": "Test",
                "max_turns": 10,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.05},
            "agents": [
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "Nation_A", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(**config_data)
        assert "duplicate" in str(exc_info.value).lower()


class TestSimulationState:
    """Tests for SimulationState model."""

    def test_create_state(self) -> None:
        """Test creating a simulation state."""
        agents = {
            "Nation_A": AgentState(name="Nation_A", economic_strength=1000.0),
            "Nation_B": AgentState(name="Nation_B", economic_strength=1500.0),
        }
        global_state = GlobalState(interest_rate=0.05, total_economic_value=2500.0)

        state = SimulationState(turn=0, agents=agents, global_state=global_state)

        assert state.turn == 0
        assert len(state.agents) == 2
        assert state.agents["Nation_A"].economic_strength == 1000.0
        assert state.global_state.total_economic_value == 2500.0

    def test_state_immutability(self) -> None:
        """Test that state is immutable."""
        agents = {"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)}
        global_state = GlobalState(interest_rate=0.05, total_economic_value=1000.0)
        state = SimulationState(turn=0, agents=agents, global_state=global_state)

        with pytest.raises(ValidationError):
            state.turn = 1  # type: ignore

        with pytest.raises(ValidationError):
            state.agents["Nation_A"].economic_strength = 2000.0  # type: ignore

    def test_state_copy_with_update(self) -> None:
        """Test creating new state with updates."""
        agents = {"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)}
        global_state = GlobalState(interest_rate=0.05, total_economic_value=1000.0)
        state = SimulationState(turn=0, agents=agents, global_state=global_state)

        new_agents = {"Nation_A": AgentState(name="Nation_A", economic_strength=1050.0)}
        new_state = state.model_copy(update={"turn": 1, "agents": new_agents})

        assert new_state.turn == 1
        assert new_state.agents["Nation_A"].economic_strength == 1050.0
        assert state.turn == 0  # Original unchanged
        assert state.agents["Nation_A"].economic_strength == 1000.0


class TestAction:
    """Tests for Action model."""

    def test_create_action(self) -> None:
        """Test creating an action."""
        action = Action(
            agent_name="Nation_A",
            action_type=ActionType.GROW,
            parameters={"strength": 1000.0},
        )

        assert action.agent_name == "Nation_A"
        assert action.action_type == ActionType.GROW
        assert action.parameters["strength"] == 1000.0
        assert not action.validated
        assert action.validation_timestamp is None

    def test_mark_validated(self) -> None:
        """Test marking an action as validated."""
        action = Action(
            agent_name="Nation_A",
            action_type=ActionType.GROW,
            parameters={},
        )

        validated_action = action.mark_validated()

        assert validated_action.validated
        assert validated_action.validation_timestamp is not None
        assert isinstance(validated_action.validation_timestamp, datetime)
        assert not action.validated  # Original unchanged

    def test_action_types(self) -> None:
        """Test all action types."""
        for action_type in [ActionType.GROW, ActionType.MAINTAIN, ActionType.DECLINE]:
            action = Action(
                agent_name="Test",
                action_type=action_type,
                parameters={},
            )
            assert action.action_type == action_type

    def test_invalid_action_type(self) -> None:
        """Test that invalid action type raises error."""
        with pytest.raises(ValidationError):
            Action(
                agent_name="Test",
                action_type="invalid",  # type: ignore
                parameters={},
            )
