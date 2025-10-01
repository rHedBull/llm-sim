"""Tests for the Always Valid Validator."""

from datetime import datetime

from llm_sim.models.state import SimulationState
from llm_sim.models.action import Action
from llm_sim.implementations.validators.always_valid import AlwaysValidValidator


class TestAlwaysValidValidator:
    """Tests for AlwaysValidValidator implementation."""

    def test_create_validator(self) -> None:
        """Test creating a validator."""
        validator = AlwaysValidValidator()
        assert validator.validation_count == 0
        assert validator.rejection_count == 0

    def test_validate_action_always_true(self, AgentState, GlobalState) -> None:
        """Test that validation always returns true."""
        validator = AlwaysValidValidator()

        state = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        # Test with valid agent
        action_valid = Action(agent_name="Nation_A", action_name="grow", parameters={})
        assert validator.validate_action(action_valid, state) is True

        # Test with non-existent agent (still returns True for AlwaysValid)
        action_invalid = Action(
            agent_name="NonExistent", action_name="grow", parameters={}
        )
        assert validator.validate_action(action_invalid, state) is True

    def test_validate_actions(self, AgentState, GlobalState) -> None:
        """Test validating multiple actions."""
        validator = AlwaysValidValidator()

        state = SimulationState(
            turn=1,
            agents={
                "Nation_A": AgentState(name="Nation_A", economic_strength=1000.0),
                "Nation_B": AgentState(name="Nation_B", economic_strength=2000.0),
            },
            global_state=GlobalState(interest_rate=0.05, total_economic_value=3000.0),
        )

        actions = [
            Action(agent_name="Nation_A", action_name="grow", parameters={}),
            Action(agent_name="Nation_B", action_name="grow", parameters={}),
        ]

        validated_actions = validator.validate_actions(actions, state)

        assert len(validated_actions) == 2
        assert all(action.validated for action in validated_actions)
        assert all(
            isinstance(action.validation_timestamp, datetime) for action in validated_actions
        )
        assert validator.validation_count == 2
        assert validator.rejection_count == 0

    def test_get_stats(self, AgentState, GlobalState) -> None:
        """Test statistics tracking."""
        validator = AlwaysValidValidator()

        # Initial stats
        stats = validator.get_stats()
        assert stats["total_validated"] == 0
        assert stats["total_rejected"] == 0
        assert stats["acceptance_rate"] == 0.0

        state = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        # Validate some actions
        actions = [
            Action(agent_name="Nation_A", action_name="grow", parameters={})
            for _ in range(5)
        ]
        validator.validate_actions(actions, state)

        stats = validator.get_stats()
        assert stats["total_validated"] == 5
        assert stats["total_rejected"] == 0
        assert stats["acceptance_rate"] == 1.0

    def test_action_marking(self, AgentState, GlobalState) -> None:
        """Test that actions are properly marked."""
        validator = AlwaysValidValidator()

        state = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        original_action = Action(agent_name="Nation_A", action_name="grow", parameters={})
        assert not original_action.validated
        assert original_action.validation_timestamp is None

        validated_actions = validator.validate_actions([original_action], state)

        # Original should be unchanged
        assert not original_action.validated
        assert original_action.validation_timestamp is None

        # Validated copy should be marked
        validated_action = validated_actions[0]
        assert validated_action.validated
        assert validated_action.validation_timestamp is not None
        assert isinstance(validated_action.validation_timestamp, datetime)
        assert validated_action.agent_name == original_action.agent_name
        assert validated_action.action_name == original_action.action_name
