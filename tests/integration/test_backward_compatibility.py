"""Integration tests for observability backward compatibility.

These tests validate that when observability is disabled or missing,
agents receive complete global state (full visibility).
Acceptance Scenarios 5-6 from spec.md.
"""

import pytest
from llm_sim.models.config import (
    SimulationConfig,
    SimulationSettings,
    EngineConfig,
    ValidatorConfig,
    AgentConfig,
    StateVariablesConfig,
    VariableDefinition,
)
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model


@pytest.fixture
def base_config():
    """Create a base simulation config for testing."""
    return SimulationConfig(
        simulation=SimulationSettings(
            name="Test Backward Compatibility",
            max_turns=5,
        ),
        engine=EngineConfig(
            type="economic",
            interest_rate=0.05,
        ),
        agents=[
            AgentConfig(name="Agent1", type="nation"),
            AgentConfig(name="Agent2", type="nation"),
            AgentConfig(name="Agent3", type="nation"),
        ],
        validator=ValidatorConfig(type="always_valid"),
        state_variables=StateVariablesConfig(
            agent_vars={
                "economic_strength": VariableDefinition(type="float", min=0, default=100.0),
                "resources": VariableDefinition(type="float", min=0, default=50.0),
                "strategy": VariableDefinition(
                    type="categorical",
                    values=["aggressive", "defensive", "balanced"],
                    default="balanced"
                ),
            },
            global_vars={
                "interest_rate": VariableDefinition(type="float", default=0.05),
                "gdp_growth": VariableDefinition(type="float", default=0.03),
                "market_volatility": VariableDefinition(type="float", min=0, max=1, default=0.1),
            },
        ),
    )


@pytest.fixture
def ground_truth_state(base_config):
    """Create a ground truth simulation state with multiple agents."""
    # Create state models from variable definitions
    AgentState = create_agent_state_model(base_config.state_variables.agent_vars)
    GlobalState = create_global_state_model(base_config.state_variables.global_vars)

    # Create agents with different state values
    agents = {
        "Agent1": AgentState(
            name="Agent1",
            economic_strength=1000.0,
            resources=200.0,
            strategy="aggressive",
        ),
        "Agent2": AgentState(
            name="Agent2",
            economic_strength=800.0,
            resources=150.0,
            strategy="defensive",
        ),
        "Agent3": AgentState(
            name="Agent3",
            economic_strength=500.0,
            resources=100.0,
            strategy="balanced",
        ),
    }

    # Create global state
    global_state = GlobalState(
        interest_rate=0.05,
        gdp_growth=0.03,
        market_volatility=0.15,
    )

    return SimulationState(
        turn=1,
        agents=agents,
        global_state=global_state,
        reasoning_chains=[],
    )


class TestBackwardCompatibility:
    """Integration tests for backward compatibility when observability is disabled or missing."""

    def test_disabled_observability_provides_full_visibility(self, base_config, ground_truth_state):
        """Test that when observability.enabled = false, agents receive complete global state.

        Acceptance Scenario 5:
        Given: observability.enabled = false
        When: Agent requests observations
        Then: Receives complete global state

        Expected: FAIL until construct_observation is implemented
        """
        from llm_sim.models.observation import construct_observation
        from llm_sim.infrastructure.observability.config import (
            ObservabilityConfig,
            VariableVisibilityConfig,
        )

        # Create observability config with enabled=false
        observability_config = ObservabilityConfig(
            enabled=False,
            variable_visibility=VariableVisibilityConfig(
                external=["economic_strength"],
                internal=["resources", "strategy"],
            ),
            matrix=[],
        )

        # Construct observation for Agent1 with disabled observability
        observation = construct_observation(
            observer_id="Agent1",
            ground_truth=ground_truth_state,
            config=observability_config,
        )

        # Assert observation equals ground truth (full visibility)
        assert observation.turn == ground_truth_state.turn
        assert set(observation.agents.keys()) == set(ground_truth_state.agents.keys())

        # Verify all agents are present with all their variables
        for agent_name in ground_truth_state.agents:
            assert agent_name in observation.agents
            ground_agent = ground_truth_state.agents[agent_name]
            obs_agent = observation.agents[agent_name]

            # Check all fields match
            assert obs_agent.name == ground_agent.name
            assert obs_agent.economic_strength == ground_agent.economic_strength
            assert obs_agent.resources == ground_agent.resources
            assert obs_agent.strategy == ground_agent.strategy

        # Verify all global state variables are present and unmodified
        assert observation.global_state.interest_rate == ground_truth_state.global_state.interest_rate
        assert observation.global_state.gdp_growth == ground_truth_state.global_state.gdp_growth
        assert observation.global_state.market_volatility == ground_truth_state.global_state.market_volatility

        # Verify reasoning chains are empty (as per spec)
        assert observation.reasoning_chains == []

    def test_missing_observability_config_provides_full_visibility(self, base_config, ground_truth_state):
        """Test that when no observability section exists, agents receive complete global state.

        Acceptance Scenario 6:
        Given: No observability section in config
        When: Agent requests observations
        Then: Receives complete global state

        Expected: FAIL until construct_observation is implemented
        """
        from llm_sim.models.observation import construct_observation

        # Verify base_config has no observability section
        assert not hasattr(base_config, "observability") or base_config.observability is None

        # Attempt to construct observation with missing observability config
        # Should handle None gracefully and return full visibility
        observation = construct_observation(
            observer_id="Agent1",
            ground_truth=ground_truth_state,
            config=None,  # No observability config
        )

        # Assert observation equals ground truth (full visibility)
        assert observation.turn == ground_truth_state.turn
        assert set(observation.agents.keys()) == set(ground_truth_state.agents.keys())

        # Verify all agents are present with all their variables
        for agent_name in ground_truth_state.agents:
            assert agent_name in observation.agents
            ground_agent = ground_truth_state.agents[agent_name]
            obs_agent = observation.agents[agent_name]

            # Check all fields match
            assert obs_agent.name == ground_agent.name
            assert obs_agent.economic_strength == ground_agent.economic_strength
            assert obs_agent.resources == ground_agent.resources
            assert obs_agent.strategy == ground_agent.strategy

        # Verify all global state variables are present
        for var_name in base_config.state_variables.global_vars.keys():
            assert hasattr(observation.global_state, var_name)
            ground_value = getattr(ground_truth_state.global_state, var_name)
            obs_value = getattr(observation.global_state, var_name)
            assert obs_value == ground_value

        # Verify reasoning chains are empty (as per spec)
        assert observation.reasoning_chains == []
