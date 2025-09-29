"""Specific integration tests for NationAgent implementation."""

import pytest

from src.llm_sim.agents.nation import NationAgent
from src.llm_sim.models.state import SimulationState, AgentState, GlobalState
from src.llm_sim.models.action import ActionType
from src.llm_sim.orchestrator import SimulationOrchestrator
from src.llm_sim.models.config import SimulationConfig


class TestNationAgentImplementation:
    """Tests that verify the actual NationAgent implementation logic."""

    def test_nation_agent_initialization(self) -> None:
        """Test NationAgent initialization with different strategies."""
        # Test default strategy
        agent_default = NationAgent(name="DefaultNation")
        assert agent_default.name == "DefaultNation"
        assert agent_default.strategy == "grow"

        # Test explicit grow strategy
        agent_grow = NationAgent(name="GrowNation", strategy="grow")
        assert agent_grow.strategy == "grow"

        # Test maintain strategy
        agent_maintain = NationAgent(name="MaintainNation", strategy="maintain")
        assert agent_maintain.strategy == "maintain"

        # Test decline strategy
        agent_decline = NationAgent(name="DeclineNation", strategy="decline")
        assert agent_decline.strategy == "decline"

        # Test invalid strategy
        with pytest.raises(ValueError, match="Invalid strategy 'invalid'"):
            NationAgent(name="InvalidNation", strategy="invalid")

    def test_nation_agent_state_tracking(self) -> None:
        """Test that NationAgent properly tracks received state."""
        agent = NationAgent(name="TrackingNation", strategy="grow")

        # Initially no state
        assert agent.get_current_state() is None

        # Create and send state
        state1 = SimulationState(
            turn=1,
            agents={"TrackingNation": AgentState(name="TrackingNation", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )
        agent.receive_state(state1)

        # Verify state was stored
        stored_state = agent.get_current_state()
        assert stored_state is not None
        assert stored_state.turn == 1
        assert stored_state.agents["TrackingNation"].economic_strength == 1000.0

        # Update with new state
        state2 = SimulationState(
            turn=2,
            agents={"TrackingNation": AgentState(name="TrackingNation", economic_strength=1050.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1050.0),
        )
        agent.receive_state(state2)

        # Verify state was updated
        updated_state = agent.get_current_state()
        assert updated_state.turn == 2
        assert updated_state.agents["TrackingNation"].economic_strength == 1050.0

    def test_nation_agent_action_decision_logic(self) -> None:
        """Test the actual decision logic of NationAgent."""
        # Test each strategy produces correct action type
        strategies_and_types = [
            ("grow", ActionType.GROW),
            ("maintain", ActionType.MAINTAIN),
            ("decline", ActionType.DECLINE),
        ]

        for strategy, expected_type in strategies_and_types:
            agent = NationAgent(name=f"TestNation_{strategy}", strategy=strategy)

            state = SimulationState(
                turn=5,
                agents={
                    f"TestNation_{strategy}": AgentState(
                        name=f"TestNation_{strategy}", economic_strength=1234.56
                    )
                },
                global_state=GlobalState(interest_rate=0.05, total_economic_value=1234.56),
            )

            action = agent.decide_action(state)

            # Verify action properties
            assert action.agent_name == f"TestNation_{strategy}"
            assert action.action_type == expected_type
            assert action.parameters["strength"] == 1234.56
            assert not action.validated  # Actions start unvalidated

    def test_nation_agent_error_handling(self) -> None:
        """Test NationAgent error handling for edge cases."""
        agent = NationAgent(name="TestNation", strategy="grow")

        # Test with state that doesn't contain this agent
        wrong_state = SimulationState(
            turn=1,
            agents={"OtherNation": AgentState(name="OtherNation", economic_strength=1000.0)},
            global_state=GlobalState(interest_rate=0.05, total_economic_value=1000.0),
        )

        # Should raise KeyError when agent not in state
        with pytest.raises(KeyError, match="TestNation"):
            agent.decide_action(wrong_state)

    def test_nation_agent_in_full_simulation(self) -> None:
        """Test NationAgent behavior in a complete simulation."""
        config_data = {
            "simulation": {
                "name": "Agent Test",
                "max_turns": 5,
                "termination": {},
            },
            "engine": {"type": "economic", "interest_rate": 0.1},
            "agents": [
                {"name": "TestNation1", "type": "nation", "initial_economic_strength": 1000.0},
                {"name": "TestNation2", "type": "nation", "initial_economic_strength": 2000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "INFO", "format": "json"},
        }

        config = SimulationConfig(**config_data)

        # Create orchestrator with specific strategies
        orchestrator = SimulationOrchestrator(
            config,
            agent_strategies={
                "TestNation1": "grow",
                "TestNation2": "maintain",
            },
        )

        # Verify agents were created with correct strategies
        assert orchestrator.agents[0].name == "TestNation1"
        assert orchestrator.agents[0].strategy == "grow"
        assert orchestrator.agents[1].name == "TestNation2"
        assert orchestrator.agents[1].strategy == "maintain"

        # Run simulation
        result = orchestrator.run()

        # Verify agents participated in all turns
        assert result["stats"]["validation"]["total_validated"] == 10  # 2 agents * 5 turns

        # Check that agents' actions were processed
        for state in result["history"][1:]:  # Skip initial state
            # Both agents should be present in each state
            assert "TestNation1" in state.agents
            assert "TestNation2" in state.agents

    def test_nation_agent_strategy_persistence(self) -> None:
        """Test that agent strategy persists throughout simulation."""
        agent = NationAgent(name="PersistentNation", strategy="decline")

        # Create multiple states and verify strategy doesn't change
        for turn in range(5):
            state = SimulationState(
                turn=turn,
                agents={
                    "PersistentNation": AgentState(
                        name="PersistentNation", economic_strength=1000.0 * (1.1**turn)
                    )
                },
                global_state=GlobalState(interest_rate=0.1, total_economic_value=1000.0 * (1.1**turn)),
            )

            action = agent.decide_action(state)

            # Strategy should always produce DECLINE action
            assert action.action_type == ActionType.DECLINE
            assert agent.strategy == "decline"  # Strategy shouldn't change

    def test_nation_agent_parameter_passing(self) -> None:
        """Test that NationAgent correctly passes parameters in actions."""
        agent = NationAgent(name="ParamNation", strategy="grow")

        # Test with various economic strength values
        test_values = [100.0, 1234.56, 99999.99, 0.01]

        for value in test_values:
            state = SimulationState(
                turn=1,
                agents={"ParamNation": AgentState(name="ParamNation", economic_strength=value)},
                global_state=GlobalState(interest_rate=0.05, total_economic_value=value),
            )

            action = agent.decide_action(state)

            # Verify the strength parameter matches the agent's current strength
            assert action.parameters["strength"] == value
            assert action.agent_name == "ParamNation"