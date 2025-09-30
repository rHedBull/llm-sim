"""Tests for the Economic Engine."""


from llm_sim.models.state import SimulationState, AgentState, GlobalState
from llm_sim.models.action import Action, ActionType
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    TerminationConditions,
    EngineConfig,
    AgentConfig,
    ValidatorConfig,
    LoggingConfig,
)
from llm_sim.engines.economic import EconomicEngine


class TestEconomicEngine:
    """Tests for EconomicEngine implementation."""

    def test_initialize_state(self) -> None:
        """Test state initialization from config."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=1000.0),
                AgentConfig(name="Nation_B", type="nation", initial_economic_strength=2000.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)
        state = engine.initialize_state()

        assert state.turn == 0
        assert len(state.agents) == 2
        assert state.agents["Nation_A"].economic_strength == 1000.0
        assert state.agents["Nation_B"].economic_strength == 2000.0
        assert state.global_state.interest_rate == 0.05
        assert state.global_state.total_economic_value == 3000.0

    def test_apply_engine_rules(self) -> None:
        """Test interest rate application."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.10),
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=1000.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)
        initial_state = engine.initialize_state()
        engine._state = initial_state

        new_state = engine.apply_engine_rules(initial_state)

        assert new_state.turn == 1
        assert new_state.agents["Nation_A"].economic_strength == 1100.0  # 1000 * 1.10
        assert new_state.global_state.total_economic_value == 1100.0

    def test_apply_actions_grow(self) -> None:
        """Test applying growth actions."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=1000.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)
        state = engine.initialize_state()
        engine._state = state

        actions = [
            Action(
                agent_name="Nation_A",
                action_type=ActionType.GROW,
                parameters={},
                validated=True,
            )
        ]

        new_state = engine.apply_actions(actions)
        assert (
            new_state.agents["Nation_A"].economic_strength == 1000.0
        )  # No change in apply_actions

    def test_check_termination_max_turns(self) -> None:
        """Test termination by max turns."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=5, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)

        state_turn_4 = SimulationState(
            turn=4, agents={}, global_state=GlobalState(interest_rate=0.05, total_economic_value=0)
        )
        assert not engine.check_termination(state_turn_4)

        state_turn_5 = SimulationState(
            turn=5, agents={}, global_state=GlobalState(interest_rate=0.05, total_economic_value=0)
        )
        assert engine.check_termination(state_turn_5)

    def test_check_termination_min_value(self) -> None:
        """Test termination by minimum value."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test",
                max_turns=100,
                termination=TerminationConditions(min_value=50.0),
            ),
            engine=EngineConfig(type="economic", interest_rate=-0.5),  # Negative interest
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=100.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)

        state_above_min = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=60.0)},
            global_state=GlobalState(interest_rate=-0.5, total_economic_value=60.0),
        )
        assert not engine.check_termination(state_above_min)

        state_below_min = SimulationState(
            turn=2,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=40.0)},
            global_state=GlobalState(interest_rate=-0.5, total_economic_value=40.0),
        )
        assert engine.check_termination(state_below_min)

    def test_check_termination_max_value(self) -> None:
        """Test termination by maximum value."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test",
                max_turns=100,
                termination=TerminationConditions(max_value=5000.0),
            ),
            engine=EngineConfig(type="economic", interest_rate=0.2),
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=1000.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)

        state_below_max = SimulationState(
            turn=1,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=4000.0)},
            global_state=GlobalState(interest_rate=0.2, total_economic_value=4000.0),
        )
        assert not engine.check_termination(state_below_max)

        state_above_max = SimulationState(
            turn=2,
            agents={"Nation_A": AgentState(name="Nation_A", economic_strength=6000.0)},
            global_state=GlobalState(interest_rate=0.2, total_economic_value=6000.0),
        )
        assert engine.check_termination(state_above_max)

    def test_run_turn(self) -> None:
        """Test running a complete turn."""
        config = SimulationConfig(
            simulation=SimulationSettings(
                name="Test", max_turns=10, termination=TerminationConditions()
            ),
            engine=EngineConfig(type="economic", interest_rate=0.05),
            agents=[
                AgentConfig(name="Nation_A", type="nation", initial_economic_strength=1000.0),
            ],
            validator=ValidatorConfig(type="always_valid"),
            logging=LoggingConfig(),
        )

        engine = EconomicEngine(config)
        initial_state = engine.initialize_state()
        engine._state = initial_state

        actions = [
            Action(
                agent_name="Nation_A",
                action_type=ActionType.GROW,
                parameters={},
                validated=True,
            )
        ]

        new_state = engine.run_turn(actions)

        assert new_state.turn == 1
        assert new_state.agents["Nation_A"].economic_strength == 1050.0  # 1000 * 1.05
        assert engine.get_current_state() == new_state
        assert engine._turn_counter == 1
