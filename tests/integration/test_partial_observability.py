"""Integration tests for partial observability feature.

These tests validate acceptance scenarios 1-4 from specs/008-partial-observability-agents/spec.md.
Expected to FAIL initially (construct_observation not yet implemented).

Tests:
- T004: Agent receives filtered observations based on matrix
- T005: External observer sees only public variables
- T006: Insider observer sees all variables
- T007: Unaware agent completely invisible
"""

import pytest
from pydantic import ValidationError

from llm_sim.models.config import VariableDefinition
from llm_sim.models.state import SimulationState, create_agent_state_model, create_global_state_model


# Test will use construct_observation once implemented
# from llm_sim.models.observation import construct_observation


@pytest.fixture
def partial_observability_config():
    """Configuration for partial observability tests.

    Defines 3 agents with asymmetric observability:
    - Agent1: sees Agent2 (external, 0.2 noise), doesn't see Agent3 (unaware)
    - Agent2: sees Agent1 (unaware), sees Agent3 (insider, 0.05 noise)
    - Agent3: sees Agent1 (external, 0.3 noise), sees Agent2 (external, 0.1 noise)
    """
    return {
        "observability": {
            "enabled": True,
            "variable_visibility": {
                "external": ["economic_strength", "position"],
                "internal": ["resources", "strategy", "hidden_reserves"]
            },
            "matrix": [
                # Agent1's view
                ["Agent1", "Agent1", "insider", 0.0],      # Self - always perfect
                ["Agent1", "Agent2", "external", 0.2],     # Sees public vars with noise
                ["Agent1", "Agent3", "unaware", None],     # Invisible

                # Agent2's view
                ["Agent2", "Agent2", "insider", 0.0],
                ["Agent2", "Agent1", "unaware", None],
                ["Agent2", "Agent3", "insider", 0.05],     # Privileged access

                # Agent3's view
                ["Agent3", "Agent3", "insider", 0.0],
                ["Agent3", "Agent1", "external", 0.3],
                ["Agent3", "Agent2", "external", 0.1],
            ]
        }
    }


@pytest.fixture
def agent_variable_definitions():
    """Variable definitions for test agents with both external and internal variables."""
    return {
        # External (public) variables
        "economic_strength": VariableDefinition(type="float", min=0.0, max=10000.0, default=1000.0),
        "position": VariableDefinition(type="int", min=0, max=100, default=50),

        # Internal (private) variables
        "resources": VariableDefinition(type="float", min=0.0, max=5000.0, default=500.0),
        "strategy": VariableDefinition(
            type="categorical",
            values=["aggressive", "defensive", "neutral"],
            default="neutral"
        ),
        "hidden_reserves": VariableDefinition(type="float", min=0.0, max=1000.0, default=100.0),
    }


@pytest.fixture
def global_variable_definitions():
    """Global state variable definitions with external and internal variables."""
    return {
        # External global variables
        "interest_rate": VariableDefinition(type="float", min=0.0, max=1.0, default=0.05),
        "market_index": VariableDefinition(type="float", min=0.0, max=10000.0, default=1000.0),

        # Internal global variables
        "central_bank_reserves": VariableDefinition(type="float", min=0.0, max=100000.0, default=10000.0),
    }


@pytest.fixture
def ground_truth_state(agent_variable_definitions, global_variable_definitions):
    """Create a ground truth simulation state with 3 agents."""
    AgentState = create_agent_state_model(agent_variable_definitions)
    GlobalState = create_global_state_model(global_variable_definitions)

    agents = {
        "Agent1": AgentState(
            name="Agent1",
            economic_strength=1000.0,
            position=10,
            resources=500.0,
            strategy="aggressive",
            hidden_reserves=200.0
        ),
        "Agent2": AgentState(
            name="Agent2",
            economic_strength=1500.0,
            position=20,
            resources=750.0,
            strategy="defensive",
            hidden_reserves=150.0
        ),
        "Agent3": AgentState(
            name="Agent3",
            economic_strength=2000.0,
            position=30,
            resources=1000.0,
            strategy="neutral",
            hidden_reserves=300.0
        ),
    }

    global_state = GlobalState(
        interest_rate=0.05,
        market_index=1200.0,
        central_bank_reserves=15000.0
    )

    return SimulationState(
        turn=1,
        agents=agents,
        global_state=global_state,
        reasoning_chains=[]
    )


def test_agent_receives_filtered_observations_based_on_matrix(
    ground_truth_state, partial_observability_config
):
    """T004: Acceptance Scenario 1 - Agent receives filtered observations.

    Given: 3 agents with different observability levels
    When: Agent1 requests current state
    Then: Agent1 sees Agent2 (external) but not Agent3 (unaware)

    Expected: FAIL (construct_observation not yet implemented)
    """
    from llm_sim.models.observation import construct_observation
    from llm_sim.infrastructure.observability.config import ObservabilityConfig

    obs_config = ObservabilityConfig(**partial_observability_config["observability"])

    observation = construct_observation(
        observer_id="Agent1",
        ground_truth=ground_truth_state,
        config=obs_config
    )

    # Agent1 should see itself and Agent2, but NOT Agent3 (unaware)
    assert "Agent1" in observation.agents
    assert "Agent2" in observation.agents
    assert "Agent3" not in observation.agents

    # Agent1 should see itself with perfect information (insider)
    agent1_obs = observation.agents["Agent1"]
    assert agent1_obs.economic_strength == 1000.0  # Perfect, no noise
    assert agent1_obs.resources == 500.0  # Can see internal vars

    # Agent1 should see Agent2 with external variables only (and noise applied)
    agent2_obs = observation.agents["Agent2"]
    # External variables should exist
    assert hasattr(agent2_obs, "economic_strength")
    assert hasattr(agent2_obs, "position")
    # Note: Exact values will differ due to 0.2 noise factor
    # Internal variables should NOT exist
    assert not hasattr(agent2_obs, "resources")
    assert not hasattr(agent2_obs, "strategy")
    assert not hasattr(agent2_obs, "hidden_reserves")


def test_external_observer_sees_only_public_variables(
    ground_truth_state, partial_observability_config
):
    """T005: Acceptance Scenario 2 - External observer sees only public variables.

    Given: Agent with external access to another agent
    When: Observer requests observations
    Then: Only external variables visible, internal hidden

    Expected: FAIL (variable filtering not yet implemented)
    """
    from llm_sim.models.observation import construct_observation
    from llm_sim.infrastructure.observability.config import ObservabilityConfig

    obs_config = ObservabilityConfig(**partial_observability_config["observability"])

    # Agent1 has "external" level access to Agent2
    observation = construct_observation(
        observer_id="Agent1",
        ground_truth=ground_truth_state,
        config=obs_config
    )

    agent2_obs = observation.agents["Agent2"]

    # Should have external variables: economic_strength, position
    assert hasattr(agent2_obs, "economic_strength")
    assert hasattr(agent2_obs, "position")

    # External variables should have noise applied (0.2 noise factor)
    # For floats, values should be within noise bounds but typically not exact
    ground_truth_agent2 = ground_truth_state.agents["Agent2"]
    assert agent2_obs.economic_strength != ground_truth_agent2.economic_strength  # Noise applied

    # For integers, noise is applied but may round to same value - check it's within bounds
    # Position can stay same after rounding, so just verify it's in valid range
    assert isinstance(agent2_obs.position, int)
    # Noise of 0.2 on value 20 gives range [16, 24], so any int in that range is valid
    assert 16 <= agent2_obs.position <= 24

    # Should NOT have internal variables: resources, strategy, hidden_reserves
    assert not hasattr(agent2_obs, "resources")
    assert not hasattr(agent2_obs, "strategy")
    assert not hasattr(agent2_obs, "hidden_reserves")


def test_insider_observer_sees_all_variables(
    ground_truth_state, partial_observability_config
):
    """T006: Acceptance Scenario 3 - Insider observer sees all variables.

    Given: Agent with insider access
    When: Observer requests observations
    Then: All variables visible with minimal noise

    Expected: FAIL (insider filtering not yet implemented)
    """
    from llm_sim.models.observation import construct_observation
    from llm_sim.infrastructure.observability.config import ObservabilityConfig

    obs_config = ObservabilityConfig(**partial_observability_config["observability"])

    # Agent2 has "insider" level access to Agent3 (0.05 noise)
    observation = construct_observation(
        observer_id="Agent2",
        ground_truth=ground_truth_state,
        config=obs_config
    )

    agent3_obs = observation.agents["Agent3"]

    # Should have ALL variables (both external and internal)
    assert hasattr(agent3_obs, "economic_strength")
    assert hasattr(agent3_obs, "position")
    assert hasattr(agent3_obs, "resources")
    assert hasattr(agent3_obs, "strategy")
    assert hasattr(agent3_obs, "hidden_reserves")

    # All variables should exist and be accessible
    assert agent3_obs.economic_strength is not None
    assert agent3_obs.position is not None
    assert agent3_obs.resources is not None
    assert agent3_obs.strategy is not None
    assert agent3_obs.hidden_reserves is not None

    # With 0.05 noise, values should be very close to ground truth
    ground_truth_agent3 = ground_truth_state.agents["Agent3"]
    noise_tolerance = 0.05  # 5% noise

    # Numeric values should be within noise bounds
    assert abs(agent3_obs.economic_strength - ground_truth_agent3.economic_strength) <= \
           ground_truth_agent3.economic_strength * noise_tolerance
    assert abs(agent3_obs.resources - ground_truth_agent3.resources) <= \
           ground_truth_agent3.resources * noise_tolerance


def test_unaware_agent_completely_invisible(
    ground_truth_state, partial_observability_config
):
    """T007: Acceptance Scenario 4 - Unaware agent completely invisible.

    Given: Agent marked unaware of target
    When: Observer requests observations
    Then: Target not in observation.agents dict

    Expected: FAIL (unaware filtering not yet implemented)
    """
    from llm_sim.models.observation import construct_observation
    from llm_sim.infrastructure.observability.config import ObservabilityConfig

    obs_config = ObservabilityConfig(**partial_observability_config["observability"])

    # Agent1 is "unaware" of Agent3
    observation = construct_observation(
        observer_id="Agent1",
        ground_truth=ground_truth_state,
        config=obs_config
    )

    # Agent3 should be completely absent from observation
    assert "Agent3" not in observation.agents

    # Agent1 should still see itself and Agent2
    assert "Agent1" in observation.agents
    assert "Agent2" in observation.agents

    # Only 2 agents in observation (not 3)
    assert len(observation.agents) == 2

    # Verify Agent2 is also "unaware" of Agent1
    observation_agent2 = construct_observation(
        observer_id="Agent2",
        ground_truth=ground_truth_state,
        config=obs_config
    )

    # Agent1 should be completely absent from Agent2's observation
    assert "Agent1" not in observation_agent2.agents
    assert "Agent2" in observation_agent2.agents  # Self
    assert "Agent3" in observation_agent2.agents  # Insider access
    assert len(observation_agent2.agents) == 2
