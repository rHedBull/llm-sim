"""Unit tests for LifecycleValidator."""

import pytest
from llm_sim.infrastructure.lifecycle.validator import LifecycleValidator
from llm_sim.models.state import SimulationState, create_agent_state_model


@pytest.fixture
def state():
    AgentState = create_agent_state_model({})
    GlobalState = create_agent_state_model({})
    return SimulationState(
        turn=1,
        agents={
            "agent1": AgentState(name="agent1"),
            "agent2": AgentState(name="agent2"),
        },
        global_state=GlobalState(name="global"),
    )


@pytest.fixture
def validator():
    return LifecycleValidator()


class TestValidateAdd:
    def test_valid_add(self, validator, state):
        result = validator.validate_add("new_agent", state)
        assert result.valid is True

    def test_add_at_max_limit(self, validator):
        AgentState = create_agent_state_model({})
        GlobalState = create_agent_state_model({})
        agents = {f"agent{i}": AgentState(name=f"agent{i}") for i in range(25)}
        state = SimulationState(
            turn=1,
            agents=agents,
            global_state=GlobalState(name="global"),
        )

        result = validator.validate_add("new_agent", state)
        assert result.valid is False
        assert "Maximum agent count" in result.reason


class TestValidateRemove:
    def test_valid_remove(self, validator, state):
        result = validator.validate_remove("agent1", state)
        assert result.valid is True

    def test_remove_nonexistent(self, validator, state):
        result = validator.validate_remove("nonexistent", state)
        assert result.valid is False
        assert "does not exist" in result.reason


class TestValidatePause:
    def test_valid_pause(self, validator, state):
        result = validator.validate_pause("agent1", None, state)
        assert result.valid is True

    def test_valid_pause_with_auto_resume(self, validator, state):
        result = validator.validate_pause("agent1", 5, state)
        assert result.valid is True

    def test_pause_nonexistent(self, validator, state):
        result = validator.validate_pause("nonexistent", None, state)
        assert result.valid is False
        assert "does not exist" in result.reason

    def test_pause_already_paused(self, validator, state):
        state.paused_agents.add("agent1")
        result = validator.validate_pause("agent1", None, state)
        assert result.valid is False
        assert "already paused" in result.reason

    def test_pause_invalid_auto_resume_zero(self, validator, state):
        result = validator.validate_pause("agent1", 0, state)
        assert result.valid is False
        assert "must be positive" in result.reason

    def test_pause_invalid_auto_resume_negative(self, validator, state):
        result = validator.validate_pause("agent1", -1, state)
        assert result.valid is False
        assert "must be positive" in result.reason


class TestValidateResume:
    def test_valid_resume(self, validator, state):
        state.paused_agents.add("agent1")
        result = validator.validate_resume("agent1", state)
        assert result.valid is True

    def test_resume_not_paused(self, validator, state):
        result = validator.validate_resume("agent1", state)
        assert result.valid is False
        assert "not paused" in result.reason

    def test_resume_nonexistent(self, validator, state):
        result = validator.validate_resume("nonexistent", state)
        assert result.valid is False
        assert "does not exist" in result.reason
